# modules/canvas.py
import os
import re
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = 1600
H = 800
PAD = 48

BgTop = (14, 18, 32)
BgBot = (6, 8, 16)
GlassFill = (255, 255, 255, 28)
TextTitle = (246, 248, 255, 255)
TextSub = (188, 196, 220, 255)
TextDim = (150, 158, 186, 255)

# Cache
_bg_cache = None
_mask_cache = {}
_font_cache = {}

# ================= FONT =================
def Font(size, bold=False):
    key = f"{size}_{bold}"
    if key in _font_cache:
        return _font_cache[key]
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_fonts_dir = os.path.join(base_dir, "data", "fonts")
    
    paths = [
        os.path.join(local_fonts_dir, "Roboto-Regular.ttf"),
        os.path.join(local_fonts_dir, "DroidSans.ttf"),
        os.path.join(local_fonts_dir, "DejaVuSans.ttf"),
        os.path.join(local_fonts_dir, "NotoSans-Regular.ttf"),
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/DroidSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    bold_paths = [
        os.path.join(local_fonts_dir, "Roboto-Bold.ttf"),
        os.path.join(local_fonts_dir, "DroidSans-Bold.ttf"),
        os.path.join(local_fonts_dir, "DejaVuSans-Bold.ttf"),
        os.path.join(local_fonts_dir, "NotoSans-Bold.ttf"),
        "/system/fonts/Roboto-Bold.ttf",
        "/system/fonts/DroidSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\tahomabd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in (bold_paths if bold else paths):
        try:
            font = ImageFont.truetype(p, int(size))
            _font_cache[key] = font
            return font
        except:
            pass
    font = ImageFont.load_default()
    _font_cache[key] = font
    return font

def FitText(draw, text, font, max_width):
    text = str(text or "")
    if draw.textlength(text, font=font) <= max_width:
        return text
    ell = "..."
    max_w = max_width - draw.textlength(ell, font=font)
    out = ""
    for ch in text:
        if draw.textlength(out + ch, font=font) > max_w:
            break
        out += ch
    return out + ell

# ================= MASK =================
def RoundMask(w, h, r, aa=4):
    key = f"{w}_{h}_{r}_{aa}"
    if key in _mask_cache:
        return _mask_cache[key]
    
    mw, mh = w * aa, h * aa
    mr = int(min(r, w // 2, h // 2) * aa)
    m = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, mw, mh), mr, fill=255)
    result = m.resize((w, h), Image.LANCZOS)
    _mask_cache[key] = result
    return result

# ================= SOFT SHADOW =================
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

# ================= GLASS EFFECT =================
def Glass(img, box, radius=36, alpha=GlassFill, blur=24, aa=4):
    x1, y1, x2, y2 = map(int, box)
    bw, bh = x2 - x1, y2 - y1
    
    # Soft shadow
    SoftShadow(img, box, radius, Blur=26, Offset=(0, 10), Alpha=90)
    
    # Blur background
    blur_img = img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blur_img, Image.new("RGBA", (bw, bh), alpha))
    mask = RoundMask(bw, bh, radius, aa=aa)
    img.paste(layer, (x1, y1), mask)

def Gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    step = 2
    for y in range(0, h, step):
        t = y / max(1, h - 1)
        color = (
            int(BgTop[0] * (1 - t) + BgBot[0] * t),
            int(BgTop[1] * (1 - t) + BgBot[1] * t),
            int(BgTop[2] * (1 - t) + BgBot[2] * t),
        )
        d.rectangle((0, y, w, y + step), fill=color)
    return img.convert("RGBA")

def Blobs(img):
    w, h = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(8):
        rr = random.randint(300, 550)
        x = random.randint(-200, w)
        y = random.randint(-200, h)
        d.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 65),
            (190, 120, 255, 58),
            (120, 255, 210, 52),
            (255, 160, 210, 48),
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(130)))

def Noise(img):
    w, h = img.size
    n = Image.new("L", (w, h))
    px = n.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(115, 145)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 16))))

def CreateBackground(w, h):
    global _bg_cache
    if _bg_cache is None:
        img = Gradient(w, h)
        Blobs(img)
        Noise(img)
        _bg_cache = img
    return _bg_cache.copy()

# ================= LOAD IMAGE =================
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

def CropSquare(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))

def CircleCrop(img, size):
    img = CropSquare(img).resize((size, size), Image.LANCZOS)
    mask = RoundMask(size, size, size // 2)
    img.putalpha(mask)
    return img

# ================= AVATAR CỐ ĐỊNH =================
MY_AVATAR_URL = "https://cdn.phototourl.com/free/2026-06-16-9b4c2a07-e02d-4b88-a842-b0cd57f49e72.jpg"
MY_NAME = "Bui Van Dat"
_my_avatar = None

def GetMyAvatar(size):
    global _my_avatar
    if _my_avatar is None:
        _my_avatar = LoadImage(MY_AVATAR_URL, (size, size))
        _my_avatar = CircleCrop(_my_avatar, size)
    return _my_avatar.copy()

def GetMyName():
    return MY_NAME

# ================= EXPORTS =================
__all__ = [
    'W', 'H', 'PAD',
    'BgTop', 'BgBot', 'GlassFill', 'TextTitle', 'TextSub', 'TextDim',
    'Font', 'FitText',
    'RoundMask', 'SoftShadow', 'Glass',
    'Gradient', 'Blobs', 'Noise', 'CreateBackground',
    'LoadImage', 'CropSquare', 'CircleCrop',
    'GetMyAvatar', 'GetMyName'
]