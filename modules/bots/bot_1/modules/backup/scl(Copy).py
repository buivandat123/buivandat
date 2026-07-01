import os
import requests
import re
import random
import time
import colorsys
import threading
import tempfile
import json
import base64
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter, ImageEnhance, ImageChops
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zlapi.models import Message, ThreadType

ADMIN = os.environ.get('ADMIN', '').split(',') if os.environ.get('ADMIN') else []
PREFIX = os.environ.get('BOT_PREFIX', '>')

Image.MAX_IMAGE_PIXELS = None

TMP_DIR = os.path.join(os.getcwd(), "assets", "temp", "scl_data")
os.makedirs(TMP_DIR, exist_ok=True)

CONFIG_FILE = "assets/settings/scl_config.json"
WATERMARK = ""

# Màu xanh cho text
COLOR_GREEN = "15a85f"

user_states = {}
client_id_cache = None
SEARCH_TIMEOUT = 60
FEEDBACK_TTL = 30000
MEDIA_TTL = 10800000

# Cache cho user info
_user_cache = {}
_user_cache_lock = threading.Lock()
_USER_CACHE_TTL = 300

# Thread pools
_download_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix='scl_dl')
_image_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='scl_img')

try:
    with open(CONFIG_FILE, "r") as f:
        config_data = json.load(f)
        SEARCH_LIMIT = config_data.get("limit", 10)
except:
    SEARCH_LIMIT = 10

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
session.mount("http://", adapter)
session.mount("https://", adapter)

# ============================================================
# ZBUG API IMPORTS & CONFIG (SoundCloud API from zBug)
# ============================================================
BASE_API = "https://api-v2.soundcloud.com"
BASE_WEB = "https://soundcloud.com"
CACHE_DIR = "./assets/cache"
os.makedirs(CACHE_DIR, exist_ok=True)
_zbug_client_id = None

def _h():
    return {"User-Agent": "Mozilla/5.0",'Authorization': 'OAuth 2-304104-1536374940-zbkU5uUKw1B9H',"Referer": BASE_WEB}

def _cid_ok(cid):
    try:
        return requests.get(f"{BASE_API}/search/tracks", params={"q": "test", "client_id": cid, "limit": 1}, headers=_h(), timeout=5).status_code == 200
    except:
        return False

def _get_zbug_client_id():
    global _zbug_client_id
    if _zbug_client_id:
        return _zbug_client_id
    fb = "vjvE4M9RytEg9W09NH1ge2VyrZPUSKo5"
    if _cid_ok(fb):
        _zbug_client_id = fb
        return fb
    try:
        from bs4 import BeautifulSoup
        s = requests.get(BASE_WEB, headers=_h(), timeout=10).text
        for t in BeautifulSoup(s, "html.parser").find_all("script", crossorigin=True)[::-1]:
            src = t.get("src")
            if not src:
                continue
            m = re.search(r'client_id:"(.*?)"', requests.get(src, headers=_h(), timeout=10).text)
            if m:
                _zbug_client_id = m.group(1)
                return _zbug_client_id
    except:
        pass
    return "vjvE4M9RytEg9W09NH1ge2VyrZPUSKo5"

def _resolve(link):
    return requests.get(f"{BASE_API}/resolve", params={"url": link, "client_id": _get_zbug_client_id()}, headers=_h(), timeout=10).json()

def search_songs_zbug(q, limit=10):
    r = requests.get(
        f"{BASE_API}/search/tracks",
        params={"q": q, "client_id": _get_zbug_client_id(), "limit": limit},
        headers=_h(),
        timeout=10
    ).json()

    return [{
        "id": t["id"],
        "title": t["title"],
        "link": t["permalink_url"],
        "artist": t["user"]["username"],
        "cover": (
            (t.get("artwork_url") or "").replace("-large", "-t500x500")
            or (t["user"].get("avatar_url") or "").replace("-large", "-t500x500")
            or None
        ),
        "duration": t.get("duration", 0) // 1000,
        "like": t.get("likes_count", 0),
        "listen": t.get("playback_count", 0),
        "comment": t.get("comment_count", 0),
    } for t in r.get("collection", [])]

def download_song_zbug(song):
    for t in _resolve(song["link"]).get("media", {}).get("transcodings", []):
        if t["format"]["protocol"] == "progressive":
            u = requests.get(t["url"], params={"client_id": _get_zbug_client_id()}, headers=_h(), timeout=10).json().get("url")
            if not u:
                return None
            fn = re.sub(r'[<>:"/\\|?*]', "_", f"{song['id']}_{song['title']}") + ".mp3"
            p = os.path.join(CACHE_DIR, fn)
            try:
                with requests.get(u, stream=True, timeout=30) as r, open(p, "wb") as f:
                    for c in r.iter_content(524288):
                        f.write(c)
                return p
            except:
                return None
    return None

# ============================================================
# ZBUG UI COMPONENTS (from zBug searchSongs.py & songsCard.py)
# ============================================================

def get_font(size, path="assets/fonts/BeVietnamPro-Bold.ttf"):
    try:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def get_title_font(size, path="font/6_1.otf"):
    try:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
        return get_font(size)
    except:
        return ImageFont.load_default()

def get_emoji_font(size, path="font/NotoEmoji-Bold.ttf"):
    try:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
        return ImageFont.truetype("seguiemj.ttf", size)
    except:
        return ImageFont.load_default()

# Font library for zBug UI (auto download fonts from GitHub)
class FontLib:
    BASE_RAW = "https://raw.githubusercontent.com/haonguyenbzzz-web/resource-libs/main"
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "font-libs")
    _cache = {}
    
    @classmethod
    def _ensure_cache_dir(cls):
        try:
            os.makedirs(cls.CACHE_DIR, exist_ok=True)
        except:
            pass
    
    @classmethod
    def GetPath(cls, filename):
        cls._ensure_cache_dir()
        import hashlib
        key = hashlib.sha1(str(filename).encode("utf-8")).hexdigest()[:16]
        out = os.path.join(cls.CACHE_DIR, f"{key}-{os.path.basename(str(filename))}")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return out
        url = f"{cls.BASE_RAW}/{filename}"
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and r.content:
                tmp = out + ".tmp"
                with open(tmp, 'wb') as f:
                    f.write(r.content)
                os.replace(tmp, out)
                return out
        except:
            pass
        return None

    @classmethod
    def Load(cls, name, size):
        import hashlib
        key = f"{name}_{size}"
        if key in cls._cache:
            return cls._cache[key]
        
        p = cls.GetPath(name)
        if p:
            try:
                font = ImageFont.truetype(p, int(size))
                cls._cache[key] = font
                return font
            except:
                pass
        
        # Fallback to common font names
        fallback_names = [
            name,
            f"font/{name}",
            f"assets/fonts/{name}",
            f"fonts/{name}",
        ]
        for fp in fallback_names:
            try:
                if os.path.exists(fp):
                    font = ImageFont.truetype(fp, int(size))
                    cls._cache[key] = font
                    return font
            except:
                pass
        
        # Last resort: use arial or default
        try:
            font = ImageFont.truetype("arial.ttf", int(size))
            cls._cache[key] = font
            return font
        except:
            pass
        
        font = ImageFont.load_default()
        cls._cache[key] = font
        return font

# ZBug DrawSongsListCard components
W = 1536
H = 768
PAD = 48

BgTop = (14, 18, 32)
BgBot = (6, 8, 16)
GlassFill = (255, 255, 255, 34)
TextTitle = (246, 248, 255, 255)
TextSub = (188, 196, 220, 255)
TextDim = (150, 158, 186, 255)

def Font(Size, Bold=False, Milker=False):
    if Milker:
        return FontLib.Load("Darley-sans.otf", Size)
    if Bold:
        return FontLib.Load("Darley-sans.otf", Size)
    return FontLib.Load("arial.ttf", Size)

def FitText(D, Text, F, MaxW):
    Text = str(Text or "")
    if D.textlength(Text, font=F) <= MaxW:
        return Text
    Ell = "..."
    MaxW2 = MaxW - D.textlength(Ell, font=F)
    Out = ""
    for Ch in Text:
        if D.textlength(Out + Ch, font=F) > MaxW2:
            break
        Out += Ch
    return Out + Ell

@lru_cache(maxsize=128)
def RoundMask(w, h, r):
    M = Image.new("L", (w, h), 0)
    ImageDraw.Draw(M).rounded_rectangle((0, 0, w, h), r, fill=255)
    return M

def SoftShadow(Img, Box, Radius, Blur=26, Offset=(0, 10), Alpha=95):
    x1, y1, x2, y2 = map(int, Box)
    bw, bh = x2 - x1, y2 - y1
    dx, dy = Offset
    Layer = Image.new("RGBA", Img.size, (0, 0, 0, 0))
    M = Image.new("L", (bw + Blur * 4, bh + Blur * 4), 0)
    ImageDraw.Draw(M).rounded_rectangle((Blur * 2, Blur * 2, Blur * 2 + bw, Blur * 2 + bh), Radius, fill=255)
    M = M.filter(ImageFilter.GaussianBlur(Blur))
    Shadow = Image.new("RGBA", M.size, (0, 0, 0, Alpha))
    Layer.paste(Shadow, (x1 + dx - Blur * 2, y1 + dy - Blur * 2), M)
    Img.alpha_composite(Layer)

def Glass(Img, Box, Radius):
    x1, y1, x2, y2 = map(int, Box)
    bw, bh = x2 - x1, y2 - y1
    SoftShadow(Img, (x1, y1, x2, y2), Radius, Blur=26, Offset=(0, 10), Alpha=90)
    Blur = Img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(24)).convert("RGBA")
    Layer = Image.alpha_composite(Blur, Image.new("RGBA", (bw, bh), GlassFill))
    Mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(Mask).rounded_rectangle((0, 0, bw, bh), Radius, fill=255)
    Img.paste(Layer, (x1, y1), Mask)

def LoadImage(Url, Size):
    Wd, Hd = map(int, Size)
    def Blank():
        return Image.new("RGBA", (Wd, Hd), (24, 26, 34, 255))
    if not Url or not isinstance(Url, str):
        return Blank()
    Url = Url.strip()
    if not (Url.startswith("http://") or Url.startswith("https://")):
        return Blank()
    Urls = [Url]
    if "sndcdn.com" in Url:
        Urls += [
            re.sub(r"-t\d+x\d+\.", "-t500x500.", Url),
            re.sub(r"-t\d+x\d+\.", "-large.", Url),
            re.sub(r"-t\d+x\d+\.", "-t300x300.", Url),
            re.sub(r"-t\d+x\d+\.", "-t200x200.", Url),
        ]
    Seen = set()
    for U in Urls:
        if not U or U in Seen:
            continue
        Seen.add(U)
        try:
            Rq = requests.get(U, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if Rq.status_code != 200 or not Rq.content:
                continue
            Img = Image.open(BytesIO(Rq.content)).convert("RGBA")
            return Img.resize((Wd, Hd), Image.LANCZOS)
        except:
            pass
    return Blank()

def DrawSongsListCard(Songs, OutPath, Title="Result..", SubTitle="", Source="SoundCloud", ItemsPerCol=10, ColGap=92, RowGap=18):
    Songs = list(Songs or [])
    if not Songs:
        os.makedirs(os.path.dirname(OutPath), exist_ok=True)
        Image.new("RGBA", (W, H), (20, 22, 30, 255)).save(OutPath)
        return OutPath

    Img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    D0 = ImageDraw.Draw(Img)

    for y in range(H):
        t = y / (H - 1)
        D0.line((0, y, W, y), fill=(
            int(BgTop[0] * (1 - t) + BgBot[0] * t),
            int(BgTop[1] * (1 - t) + BgBot[1] * t),
            int(BgTop[2] * (1 - t) + BgBot[2] * t),
            255
        ))

    Blob = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Db = ImageDraw.Draw(Blob)
    for _ in range(10):
        rr = random.randint(260, 560)
        x = random.randint(-240, W - 60)
        y = random.randint(-240, H - 60)
        Db.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 70),
            (190, 120, 255, 64),
            (120, 255, 210, 54),
            (255, 160, 210, 50),
        ]))
    Img.alpha_composite(Blob.filter(ImageFilter.GaussianBlur(140)))

    Noise = Image.new("L", (W, H))
    Px = Noise.load()
    for y in range(H):
        for x in range(W):
            Px[x, y] = random.randint(118, 142)
    Img.alpha_composite(Image.merge("RGBA", (Noise, Noise, Noise, Image.new("L", (W, H), 14))))

    Card = (PAD, PAD, W - PAD, H - PAD)
    Glass(Img, Card, 44)

    LeftW = 420
    Gap = 26
    Inner = 26

    Lx1 = PAD + Inner
    Ly1 = PAD + Inner
    Lx2 = Lx1 + LeftW
    Ly2 = H - PAD - Inner

    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = W - PAD - Inner
    Ry2 = Ly2

    LeftBox = (Lx1, Ly1, Lx2, Ly2)
    Glass(Img, LeftBox, 44)

    D = ImageDraw.Draw(Img)

    Pick = Songs[0]
    BigThumb = 320
    BigR = 44
    ThumbX = int(Lx1 + (LeftW - BigThumb) / 2)
    ThumbY = int(Ly1 + 28)

    Cover = LoadImage(Pick.get("cover"), (BigThumb, BigThumb))
    BigMask = RoundMask(BigThumb, BigThumb, BigR)
    Img.paste(Cover, (ThumbX, ThumbY), BigMask)

    TitleFont = Font(40, Bold=True)
    SubFont = Font(26)
    BadgeFont = Font(26, Milker=True)

    LT = FitText(D, Pick.get("title", "Unknown"), TitleFont, LeftW - 52)
    LA = FitText(D, Pick.get("artist", "Unknown"), SubFont, LeftW - 52)

    Tx = Lx1 + 26
    Ty = ThumbY + BigThumb + 22
    D.text((Tx, Ty), LT, font=TitleFont, fill=TextTitle)
    D.text((Tx, Ty + 52), LA, font=SubFont, fill=TextSub)

    BadgeText = str(Source or "SoundCloud")
    Bw = int(D.textlength(BadgeText, font=BadgeFont) + 72)
    Bh = 56
    Bx1 = int(Lx1 + (LeftW - Bw) / 2)
    By1 = int(Ly2 - 26 - Bh)
    Glass(Img, (Bx1, By1, Bx1 + Bw, By1 + Bh), 28)
    D.text((Bx1 + 36, By1 + 14), BadgeText, font=BadgeFont, fill=(255, 255, 255, 245))

    Items = Songs[:10]
    Cols = 2
    Rows = 5

    AreaW = int((Rx2 - Rx1) - 18 * 2)
    AreaH = int((Ry2 - Ry1) - 18 * 2)

    CGap = 26
    RGap = 18

    ColW = int((AreaW - (Cols - 1) * CGap) / Cols)
    RowH = int((AreaH - (Rows - 1) * RGap) / Rows)
    RowH = max(104, min(RowH, 126))

    Thumb = 76
    ThumbR = 22
    ThumbMask = RoundMask(Thumb, Thumb, ThumbR)

    RowTitleFont = Font(34, Bold=True)
    RowMetaFont = Font(22)
    IdxFont = Font(22)

    for i, S in enumerate(Items):
        c = i // Rows
        r = i % Rows

        x1 = int(Rx1 + 18 + c * (ColW + CGap))
        y1 = int(Ry1 + 18 + r * (RowH + RGap))
        x2 = int(x1 + ColW)
        y2 = int(y1 + RowH)

        Glass(Img, (x1, y1, x2, y2), 26)

        ix = x1 + 20
        iy = int(y1 + (RowH - Thumb) / 2)

        Cover = LoadImage(S.get("cover"), (Thumb, Thumb))
        Img.paste(Cover, (ix, iy), ThumbMask)

        Tx = ix + Thumb + 18
        MaxTextW = x2 - Tx - 20

        TitleStr = FitText(D, S.get("title", "Unknown"), RowTitleFont, MaxTextW)

        artist = str(S.get("artist", "Unknown") or "Unknown")
        dur = str(S.get("duration") or "")
        meta = f"{artist} | {dur}".strip()
        MetaStr = FitText(D, meta, RowMetaFont, MaxTextW)

        D.text((Tx, y1 + 18), TitleStr, font=RowTitleFont, fill=TextTitle)
        D.text((Tx, y1 + 18 + 46), MetaStr, font=RowMetaFont, fill=TextSub)

        Idx = str(i + 1)
        iw = int(D.textlength(Idx, font=IdxFont))
        D.text((x2 - 16 - iw, y2 - 14 - 24), Idx, font=IdxFont, fill=TextDim)

    os.makedirs(os.path.dirname(OutPath), exist_ok=True)
    Img.save(OutPath, "PNG")
    return OutPath

# ZBug draw_song_card components (Playing Card)
song_w = 1600
song_h = 600
song_pad = 64
song_r = 36

bg_top = (14, 18, 30)
bg_bot = (8, 10, 18)
g_bg = (255, 255, 255, 28)
c_title = (245, 248, 255)
c_artist = (180, 190, 215)
c_time = (150, 160, 190)

def song_font(size, bold=False, milker=False):
    name = "Milker-Bold.otf" if milker else ("Dela-gothic-one.ttf" if bold else "Darley-sans.otf")
    return FontLib.Load(name, size)

def song_fit_text(draw, text, font_obj, max_width):
    text = str(text or "")
    if draw.textlength(text, font=font_obj) <= max_width:
        return text
    ell = "..."
    max_w = max_width - draw.textlength(ell, font=font_obj)
    out = ""
    for ch in text:
        if draw.textlength(out + ch, font=font_obj) > max_w:
            break
        out += ch
    return out + ell

def song_gradient(w0, h0):
    img = Image.new("RGB", (w0, h0))
    d = ImageDraw.Draw(img)
    for y in range(h0):
        t = y / h0
        d.line((0, y, w0, y), fill=(
            int(bg_top[0] * (1 - t) + bg_bot[0] * t),
            int(bg_top[1] * (1 - t) + bg_bot[1] * t),
            int(bg_top[2] * (1 - t) + bg_bot[2] * t)
        ))
    return img.convert("RGBA")

def song_blobs(img):
    w0, h0 = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(6):
        rr = random.randint(300, 520)
        x = random.randint(-200, w0)
        y = random.randint(-200, h0)
        d.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 60),
            (190, 120, 255, 55),
            (120, 255, 200, 50)
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(120)))

def song_noise(img):
    w0, h0 = img.size
    n = Image.new("L", (w0, h0))
    px = n.load()
    for y in range(h0):
        for x in range(w0):
            px[x, y] = random.randint(120, 140)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w0, h0), 18))))

def pill_mask(bw, bh, aa=8):
    mw, mh = bw * aa, bh * aa
    rr = mh // 2
    m = Image.new("L", (mw, mh), 0)
    d = ImageDraw.Draw(m)
    d.rectangle((rr, 0, mw - rr, mh), fill=255)
    d.ellipse((0, 0, rr * 2, mh), fill=255)
    d.ellipse((mw - rr * 2, 0, mw, mh), fill=255)
    return m.resize((bw, bh), Image.LANCZOS)

def rounded_mask(bw, bh, radius, aa=4):
    mw, mh = bw * aa, bh * aa
    mr = int(min(radius, bw // 2, bh // 2) * aa)
    m = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, mw, mh), mr, fill=255)
    return m.resize((bw, bh), Image.LANCZOS)

def song_glass(canvas, box, radius=song_r, alpha=g_bg, blur=26, aa=4, pill=False):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    blur_img = canvas.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blur_img, Image.new("RGBA", (bw, bh), alpha))
    mask = pill_mask(bw, bh, aa=max(aa, 6)) if pill else rounded_mask(bw, bh, radius, aa=aa)
    canvas.paste(layer, box, mask)

def crop_square(img):
    w0, h0 = img.size
    s = min(w0, h0)
    return img.crop(((w0 - s) // 2, (h0 - s) // 2, (w0 + s) // 2, (h0 + s) // 2))

def song_load_image(url, size=(500, 500)):
    w0, h0 = size
    def blank():
        return Image.new("RGBA", (w0, h0), (25, 25, 25, 255))
    if not url or not isinstance(url, str):
        return blank()
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        return blank()
    urls = [url]
    if "sndcdn.com" in url:
        urls.append(re.sub(r"-t\d+x\d+\.", "-t500x500.", url))
        urls.append(re.sub(r"-t\d+x\d+\.", "-large.", url))
        urls.append(re.sub(r"-t\d+x\d+\.", "-t300x300.", url))
        urls.append(re.sub(r"-t\d+x\d+\.", "-t200x200.", url))
    seen = set()
    for u in urls:
        if not u or u in seen:
            continue
        seen.add(u)
        try:
            r0 = requests.get(u, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r0.status_code != 200 or not r0.content:
                continue
            im = Image.open(BytesIO(r0.content)).convert("RGBA")
            return im.resize((w0, h0), Image.LANCZOS)
        except:
            continue
    return blank()

def media_dir():
    from pathlib import Path
    return Path(__file__).resolve().parent / "media"

def load_icon(name, size):
    if name and isinstance(name, str):
        p = media_dir() / name
        try:
            if p.is_file():
                return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
        except:
            pass
    p = media_dir() / "noIcon.png"
    try:
        if p.is_file():
            return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
    except:
        pass
    return None

def circle_mask(size, aa=6):
    s = size * aa
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((0, 0, s - 1, s - 1), fill=255)
    return m.resize((size, size), Image.LANCZOS)

def draw_song_card(song, out_path):
    img = song_gradient(song_w, song_h)
    song_blobs(img)
    song_noise(img)

    card = (song_pad, song_pad, song_w - song_pad, song_h - song_pad)
    song_glass(img, card, radius=song_r, alpha=g_bg, blur=26, aa=4)

    d = ImageDraw.Draw(img)

    cover_size = 400
    cover_pad = 44
    cover = song_load_image(song.get("cover"), size=(500, 500))
    cover = crop_square(cover).resize((cover_size, cover_size), Image.LANCZOS)
    mask = Image.new("L", (cover_size, cover_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cover_size, cover_size), 28, fill=255)
    img.paste(cover, (song_pad + cover_pad, song_pad + cover_pad), mask)

    tx = song_pad + cover_pad + cover_size + 52
    ty = song_pad + 70
    right_pad = 44
    max_text_w = (song_w - song_pad) - tx - right_pad

    title_font = song_font(64, bold=True)
    artist_font = song_font(36)
    time_font = song_font(28)

    title = song_fit_text(d, song.get("title"), title_font, max_text_w)
    artist = song_fit_text(d, song.get("artist"), artist_font, max_text_w)

    d.text((tx, ty), title, font=title_font, fill=c_title)
    d.text((tx, ty + 92), artist, font=artist_font, fill=c_artist)
    d.text((tx, ty + 146), str(song.get("duration") or ""), font=time_font, fill=c_time)

    source = str(song.get("source") or "SoundCloud")
    badge_font = song_font(28, milker=True)

    icon_size = 34
    icon = load_icon(song.get("sourceIcon"), icon_size)
    icon_gap = 12
    left_pad = 22
    right_pad2 = 22

    text_w = d.textlength(source, font=badge_font)
    content_w = text_w + (icon_size + icon_gap if icon is not None else 0)

    badge_h = 52
    badge_w = int(left_pad + content_w + right_pad2)

    card_x1, card_y1, card_x2, card_y2 = song_pad, song_pad, song_w - song_pad, song_h - song_pad
    inset = 10

    badge_x = card_x2 - inset - badge_w
    badge_y = card_y2 - inset - badge_h

    if badge_x < card_x1 + inset:
        badge_x = card_x1 + inset
    if badge_y < card_y1 + inset:
        badge_y = card_y1 + inset

    badge_box = (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h)
    song_glass(img, badge_box, alpha=(255, 255, 255, 22), blur=18, pill=True)

    cx = badge_x + left_pad
    if icon is not None:
        cmask = circle_mask(icon_size)
        img.paste(icon, (int(cx), int(badge_y + (badge_h - icon_size) // 2)), cmask)
        cx += icon_size + icon_gap

    bbox = d.textbbox((0, 0), source, font=badge_font)
    th = bbox[3] - bbox[1]
    text_y = badge_y + (badge_h - th) // 2 - bbox[1]
    d.text((cx, text_y), source, font=badge_font, fill=(255, 200, 255))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def get_cached_user_info(client, uid):
    """Lấy user info với cache."""
    global _user_cache
    uid_str = str(uid)
    now = time.time()
    with _user_cache_lock:
        if uid_str in _user_cache:
            name, cached_time = _user_cache[uid_str]
            if now - cached_time < _USER_CACHE_TTL:
                return name
    try:
        user_info = client.fetchUserInfo(uid)
        name = user_info.changed_profiles.get(uid_str).displayName
        with _user_cache_lock:
            _user_cache[uid_str] = (name, now)
        return name
    except:
        return "Người dùng"

def delete_msg(client, msg_obj, thread_id, thread_type):
    try:
        msg_id = getattr(msg_obj, 'msgId', None)
        cli_msg_id = getattr(msg_obj, 'cliMsgId', None)
        
        if not msg_id and isinstance(msg_obj, dict):
            msg_id = msg_obj.get('msgId')
            cli_msg_id = msg_obj.get('cliMsgId')

        if not cli_msg_id:
            cli_msg_id = int(time.time() * 1000)

        if msg_id:
            client.undoMessage(msg_id, cli_msg_id, thread_id, thread_type)
    except:
        pass

def format_duration(seconds):
    """Format duration in seconds to MM:SS or HH:MM:SS"""
    if not seconds:
        return "00:00"
    seconds = int(seconds)
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def autosave(img, quality=95):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(tf, "JPEG", quality=quality, dpi=(100,100), optimize=True)
        return tf.name

# ============================================================
# CLEANUP THREAD
# ============================================================

def cleanup_states():
    """Dọn dẹp các trạng thái tìm kiếm đã hết hạn sau SEARCH_TIMEOUT giây."""
    while True:
        try:
            current_time = time.time()
            to_delete = []
            for aid, state in user_states.items():
                if current_time - state['time'] > SEARCH_TIMEOUT:
                    client = state.get('client')
                    if client:
                        try:
                            msg_text = f"🚦 Đã hết thời gian chọn bài."
                            client.sendMessage(Message(text=msg_text), state['thread_id'], state['thread_type'])
                            
                            m_obj = state.get('msg_obj')
                            if m_obj:
                                delete_msg(client, m_obj, state['thread_id'], state['thread_type'])
                        except: pass
                    to_delete.append(aid)
            for aid in to_delete:
                if aid in user_states: del user_states[aid]
        except: pass
        time.sleep(2)

threading.Thread(target=cleanup_states, daemon=True).start()

# ============================================================
# LEGACY EXPORTS (for backward compatibility with other modules)
# ============================================================
def get_client_id():
    """Legacy function - returns client ID."""
    return _get_zbug_client_id()

def search_songs(query, limit=10):
    """Legacy function - searches songs with old format."""
    return search_songs_zbug(query, limit)

def get_playable_url(link, client_id):
    """Legacy function - resolves playable URL."""
    try:
        track_data = _resolve(link)
        media_url = None
        for transcode in track_data.get('media', {}).get('transcodings', []):
            if transcode['format']['protocol'] == 'progressive':
                media_url = transcode['url']
                break
        if not media_url:
            return None
        r2 = requests.get(f"{media_url}?client_id={client_id}", headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        raw_url = r2.json().get('url')
        return raw_url
    except:
        return None

def download(song):
    """Legacy function - downloads song file."""
    return download_song_zbug(song)

# ============================================================
# COMMAND HANDLERS (Keeping original bot logic)
# ============================================================

def handle_scl_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id in user_states:
        client.replyMessage(Message(text="⚠️ Bạn đang có một tìm kiếm chưa hoàn tất. Nhập '0' để hủy."), message_object, thread_id, thread_type)
        return
    query = ' '.join(message.strip().split()[1:])
    client.sendReaction(message_object, "🔍", thread_id, thread_type)
    if not query:
        client.replyMessage(
            Message(text=f"➜ Vui lòng nhập từ khóa tìm kiếm.\nVí dụ:\n.scl Bài Hát Cần Tìm"),
            message_object, thread_id, thread_type, ttl=FEEDBACK_TTL
        )
        return

    try:
        user_info = client.fetchUserInfo(author_id)
        author_name = user_info.changed_profiles.get(author_id).displayName
    except: 
        author_name = "Người dùng"
    
    # Use zBug search function
    songs = search_songs_zbug(query, limit=SEARCH_LIMIT)
    if not songs:
        client.replyMessage(Message(text=f"Không tìm thấy: {query}"), message_object, thread_id, thread_type, ttl=FEEDBACK_TTL)
        return
    
    try:
        # Format songs for zBug DrawSongsListCard
        formatted_songs = []
        for song in songs:
            formatted_songs.append({
                "title": song.get("title", "Unknown"),
                "artist": song.get("artist", "Unknown"),
                "cover": song.get("cover"),
                "duration": format_duration(song.get("duration"))
            })
        
        # Use zBug DrawSongsListCard for UI
        img_path = os.path.join(os.getcwd(), "assets", "temp", "scl_data", f"sc_list_{author_id}_{int(time.time() * 1000)}.png")
        DrawSongsListCard(
            formatted_songs,
            img_path,
            Title="Kết quả tìm kiếm",
            SubTitle="Chọn số để phát bài",
            Source="SoundCloud",
        )
        
        with Image.open(img_path) as im:
            width, height = im.size
            
        owner_tag = f"🚦"
        msg_text = f"{owner_tag}\n🔍 Kết quả tìm kiếm của bạn.\n➜ Gửi số thứ tự (1-{len(songs)}) để nghe."
        
        msg = client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, width=width, height=height, ttl=120000, message=Message(text=msg_text))
        try:
            os.remove(img_path)
        except: pass
        
        user_states[author_id] = {
            'songs': songs,
            'msg_obj': msg,
            'time': time.time(),
            'thread_id': thread_id,
            'thread_type': thread_type,
            'client': client,
            'author_name': author_name
        }
    except Exception as e:
        print(f"Error SCL Image: {e}")
        client.replyMessage(Message(text="⚠️ Lỗi tạo ảnh menu."), message_object, thread_id, thread_type)

def handle_message(message, message_object, thread_id, thread_type, author_id, client):
    msg_text = message.strip()
    if author_id not in user_states: return
    state = user_states[author_id]
    if time.time() - state['time'] > SEARCH_TIMEOUT:
        del user_states[author_id]
        return
    if msg_text == "0":
        m_obj = state.get('msg_obj')
        if m_obj:
            delete_msg(client, m_obj, state['thread_id'], state['thread_type'])
        client.sendMessage(Message(text="Đã hủy."), thread_id, thread_type, ttl=FEEDBACK_TTL)
        del user_states[author_id]
        return
    if not msg_text.isdigit(): return
    choice = int(msg_text)
    songs = state['songs']
    if choice < 1 or choice > len(songs):
        return
        
    # Delete the selection image
    m_obj = state.get('msg_obj')
    if m_obj:
        delete_msg(client, m_obj, state['thread_id'], state['thread_type'])
    
    # Reply to user's message with green color for text
    song_title = songs[choice - 1].get('title', 'Unknown')
    
    # Build message text
    msg_text = f"🎶 Chờ lấy nhạc một chút, xong sẽ gọi cho hay.\n\n🎵 {song_title}\n🔊 Quality: 320kbps"
    
    from zlapi.models import MessageStyle, MultiMsgStyle
    
    green_color = COLOR_GREEN.replace("#", "")
    
    # Simply apply green color to the entire message
    msg_style = MessageStyle(
        offset=0,
        length=len(msg_text),
        style="color",
        color=green_color,
        auto_format=False
    )
    
    msg = Message(text=msg_text, style=str(msg_style))
    client.replyMessage(msg, message_object, thread_id, thread_type, ttl=FEEDBACK_TTL)
    
    del user_states[author_id]
    song = songs[choice - 1]
    mentions = message_object.mentions
    target_id = mentions[0]['uid'] if mentions else author_id
    try:
        user_info = client.fetchUserInfo(target_id)
        user_profile = user_info.changed_profiles.get(target_id)
        user_avatar = user_profile.avatar
        user_name = user_profile.displayName
    except:
        user_avatar = ""
        user_name = "User"
    client.sendReaction(message_object, "💿", thread_id, thread_type)
    
    def process_and_send():
        # Use zBug download function
        temp_file = download_song_zbug(song)
        if not temp_file or not os.path.exists(temp_file):
            client.sendMessage(Message(text="⚠️ Không thể tải file."), thread_id, thread_type, ttl=FEEDBACK_TTL)
            return
            
        try:
            file_size = os.path.getsize(temp_file)
            uploaded = client._uploadAttachment(temp_file, thread_id, thread_type)
            
            if uploaded and uploaded.get("fileUrl"):
                watermarked_url = uploaded["fileUrl"] + WATERMARK
                
                try:
                    # Use zBug draw_song_card for UI
                    card_payload = {
                        "title": song.get("title", "Unknown"),
                        "artist": song.get("artist", "Unknown"),
                        "duration": format_duration(song.get("duration")),
                        "cover": song.get("cover"),
                        "source": "SoundCloud",
                        "sourceIcon": "soundcloudIcon.png"
                    }
                    card_path = os.path.join(os.getcwd(), "assets", "temp", "scl_data", f"sc_card_{int(time.time() * 1000)}.png")
                    draw_song_card(card_payload, card_path)
                    
                    with Image.open(card_path) as im:
                        w, h = im.size
                        
                    client.sendLocalImage(card_path, thread_id=thread_id, thread_type=thread_type, width=w, height=h, ttl=FEEDBACK_TTL)
                    try:
                        os.remove(card_path)
                    except: pass
                except Exception as e:
                    print(f"Card Error: {e}")
                    
                client.sendRemoteVoice(watermarked_url, thread_id, thread_type, fileSize=file_size)
            else:
                client.sendMessage(Message(text="❌ Lỗi Upload Zalo."), thread_id, thread_type, ttl=FEEDBACK_TTL)
        except Exception as e:
            print(f"SCL DL Error: {e}")
            client.sendMessage(Message(text="⚠️ Lỗi xử lý file."), thread_id, thread_type, ttl=FEEDBACK_TTL)
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except: pass
                
    threading.Thread(target=process_and_send).start()

def Kryzis():
    return {
        'SoundCloud': handle_scl_command,
        'scl': handle_scl_command,
        'music': handle_scl_command,
        'ms': handle_scl_command,
        'message': handle_message
    }

des = {
    'version': "1.0.0",
    'credits': "Tuann",
    'description': "Tìm kiếm và phát nhạc SoundCloud",
    'power': "Thanh vien"
}
