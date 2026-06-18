# modules/canvas.py
# -*- coding: utf-8 -*-
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

def Font(size, bold=False):
    key = f"{size}_{bold}"
    if key in _font_cache:
        return _font_cache[key]
    
    paths = [
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/DroidSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    bold_paths = [
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

def Glass(img, box, radius=36, alpha=GlassFill, blur=24, aa=4):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    blur_img = img.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blur_img, Image.new("RGBA", (bw, bh), alpha))
    mask = RoundMask(bw, bh, radius, aa=aa)
    img.paste(layer, box, mask)

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

def LoadImage(url, size):
    w, h = size
    def blank():
        img = Image.new("RGBA", (w, h), (40, 45, 60, 255))
        d = ImageDraw.Draw(img)
        d.ellipse((5, 5, w-5, h-5), fill=(80, 100, 150))
        d.ellipse((w//3-15, h//3-10, w//3+5, h//3+10), fill=(255, 255, 255))
        d.ellipse((w*2//3-15, h//3-10, w*2//3+5, h//3+10), fill=(255, 255, 255))
        d.arc((w//3, h//2, w*2//3, h*3//4), 0, 180, fill=(255, 255, 255), width=6)
        return img
    if not url or not isinstance(url, str):
        return blank()
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return blank()
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.content:
            return blank()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize((w, h), Image.LANCZOS)
    except:
        return blank()

def CropSquare(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))

def CircleCrop(img, size):
    img = CropSquare(img).resize((size, size), Image.LANCZOS)
    mask = RoundMask(size, size, size // 2)
    img.putalpha(mask)
    return img

# ========== AVATAR CỐ ĐỊNH ==========
MY_AVATAR_URL = "https://cdn.phototourl.com/free/2026-06-16-9b4c2a07-e02d-4b88-a842-b0cd57f49e72.jpg"
MY_NAME = "Kryzis Bot"
_my_avatar = None

def GetMyAvatar(size):
    global _my_avatar
    if _my_avatar is None:
        _my_avatar = LoadImage(MY_AVATAR_URL, (size, size))
        _my_avatar = CircleCrop(_my_avatar, size)
    return _my_avatar.copy()

def GetMyName():
    return MY_NAME
