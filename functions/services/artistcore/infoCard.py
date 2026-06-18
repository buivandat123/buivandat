from datetime import datetime
from io import BytesIO
import os, hashlib, random, requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import emoji as emoji_lib
from functions.services.artistcore.font.fontLibs import *

cachedir = "assets/cache"

white = (245, 248, 255)
lightgray = (180, 190, 215)
dimgray = (150, 160, 190)

bgTop = (14, 18, 30)
bgBot = (8, 10, 18)
glassFill = (255, 255, 255, 28)

def IsEmoji(ch):
    return ch in emoji_lib.EMOJI_DATA

def DrawText(draw, text, font, efont, x, y, color):
    for ch in str(text or ""):
        f = efont if IsEmoji(ch) else font
        draw.text((x, y), ch, fill=color, font=f)
        bb = draw.textbbox((x, y), ch, font=f)
        x += bb[2] - bb[0]
    return x

def FitText(draw, text, font, maxw):
    text = str(text or "")
    if draw.textlength(text, font=font) <= maxw:
        return text
    ell = "..."
    lim = maxw - draw.textlength(ell, font=font)
    out = ""
    for ch in text:
        if draw.textlength(out + ch, font=font) > lim:
            break
        out += ch
    return out + ell

def LoadNetImage(url, size, timeout=10):
    w, h = size
    def blank():
        return Image.new("RGBA", (w, h), (25, 25, 25, 255))
    if not url or not isinstance(url, str):
        return blank()
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return blank()
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.content:
            return blank()
        im = Image.open(BytesIO(r.content)).convert("RGBA")
        return im.resize((w, h), Image.LANCZOS)
    except:
        return blank()

def FitCover(img, size):
    tw, th = size
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return img.resize((tw, th), Image.LANCZOS)
    s = max(tw / iw, th / ih)
    nw, nh = int(iw * s), int(ih * s)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return img.crop((x, y, x + tw, y + th))

def CropSquare(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))

def RoundedMask(bw, bh, radius, aa=4):
    mw, mh = bw * aa, bh * aa
    rr = int(min(radius, bw // 2, bh // 2) * aa)
    m = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, mw, mh), rr, fill=255)
    return m.resize((bw, bh), Image.LANCZOS)

def Glass(canvas, box, radius=36, alpha=glassFill, blur=26, aa=4):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    blurimg = canvas.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blurimg, Image.new("RGBA", (bw, bh), alpha))
    mask = RoundedMask(bw, bh, radius, aa=aa)
    canvas.paste(layer, box, mask)

def Gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(
            int(bgTop[0] * (1 - t) + bgBot[0] * t),
            int(bgTop[1] * (1 - t) + bgBot[1] * t),
            int(bgTop[2] * (1 - t) + bgBot[2] * t),
        ))
    return img.convert("RGBA")

def Blobs(img):
    w, h = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(6):
        rr = random.randint(300, 520)
        x = random.randint(-200, w)
        y = random.randint(-200, h)
        d.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 60),
            (190, 120, 255, 55),
            (120, 255, 200, 50),
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(120)))

def Noise(img):
    w, h = img.size
    n = Image.new("L", (w, h))
    px = n.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(120, 140)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 18))))

def ToDate(d):
    if not d:
        return "Ẩn"
    if isinstance(d, int):
        try:
            return datetime.fromtimestamp(d).strftime("%d/%m/%Y")
        except:
            return str(d)
    return str(d)

def ToDateMs(ts):
    if not ts:
        return "N/A"
    if isinstance(ts, int):
        try:
            v = ts / 1000 if ts > 10_000_000_000 else ts
            return datetime.fromtimestamp(v).strftime("%d/%m/%Y")
        except:
            return str(ts)
    return "N/A"

def SaveCard(img, outpath):
    os.makedirs(os.path.dirname(outpath) or ".", exist_ok=True)
    ext = (os.path.splitext(outpath)[1] or "").lower()
    if ext in (".jpg", ".jpeg"):
        img.save(outpath, quality=95, subsampling=0, optimize=True)
    else:
        img.save(outpath)
    return outpath

def PasteRoundedImage(dst, src, pos, size, radius, shadow=True):
    x, y = pos
    w, h = size
    im = CropSquare(src).resize((w, h), Image.LANCZOS)
    mask = RoundedMask(w, h, radius, aa=6)
    if shadow:
        sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle((30, 30, 30 + w, 30 + h), radius=radius, fill=(0, 0, 0, 160))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        dst.alpha_composite(sh, (x - 30, y - 24))
    dst.paste(im, (x, y), mask)

def DrawIconBadge(img, cx, cy, r, icon, iconFont):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 22), outline=(255, 255, 255, 35), width=2)
    bb = d.textbbox((0, 0), icon, font=iconFont)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    x = cx - tw // 2 - bb[0]
    y = cy - th // 2 - bb[1] - 1
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + ox, y + oy), icon, font=iconFont, fill=(0, 0, 0, 180))
    d.text((x, y), icon, font=iconFont, fill=(245, 248, 255, 255))

def FlattenRGBA(img, bg=(12, 12, 12)):
    if img.mode != "RGBA":
        return img.convert("RGB")
    base = Image.new("RGB", img.size, bg)
    base.paste(img, mask=img.split()[-1])
    return base

def CreateUserInfoCard(outpath, usinfo):
    w = 1600
    h = 600
    pad = 64
    r = 36

    coverurl = getattr(usinfo, "cover", None)
    avatarurl = getattr(usinfo, "avatar", None)

    bg = Gradient(w, h)
    if coverurl:
        cov = LoadNetImage(str(coverurl), (w, h), timeout=10)
        cov = FitCover(cov, (w, h)).filter(ImageFilter.GaussianBlur(22))
        bg = Image.alpha_composite(cov, Image.new("RGBA", (w, h), (0, 0, 0, 130)))

    Blobs(bg)
    Noise(bg)

    card = (pad, pad, w - pad, h - pad)
    Glass(bg, card, radius=r, alpha=glassFill, blur=26, aa=4)

    d = ImageDraw.Draw(bg)

    name = getattr(usinfo, "zaloName", None) or "Undefined"
    userid = getattr(usinfo, "userId", None) or "Undefined"

    g0 = getattr(usinfo, "gender", None)
    gender = "Nam" if g0 == 0 else "Nữ" if g0 == 1 else "N/A"

    biz = getattr(usinfo, "bizPkg", None)
    bizPkgId = 0
    if isinstance(biz, dict):
        bizPkgId = int(biz.get("pkgId", 0) or 0)
    else:
        bizPkgId = int(getattr(biz, "pkgId", 0) or 0)
    hasBiz = bizPkgId != 0

    dob = ToDate(getattr(usinfo, "dob", None) or getattr(usinfo, "sdob", None))
    lastaction = ToDateMs(getattr(usinfo, "lastActionTime", None))
    createtime = ToDateMs(getattr(usinfo, "createdTs", None))

    infolines = [
        ("ID", str(userid)),
        ("Giới tính", gender),
        ("Sinh nhật", str(dob)),
        ("Online gần nhất", str(lastaction)),
        ("Tạo tài khoản", str(createtime)),
        ("Business", "Có" if hasBiz else "Không"),
    ]

    namefont = FontLib.Load("Dela-gothic-one.ttf", 66)
    labelfont = FontLib.Load("Darley-sans.otf", 30)
    valfont = labelfont
    efont = FontLib.Load("emoji.ttf", 54)
    iconfont = FaLib.Font(28)

    coverSize = 350
    coverPad = 44

    avx = pad + coverPad
    avy = pad + coverPad

    av = LoadNetImage(str(avatarurl or ""), (600, 600), timeout=10)
    PasteRoundedImage(bg, av, (avx, avy), (coverSize, coverSize), radius=28, shadow=True)

    flags = [
        ("fa-briefcase", hasBiz),
        ("fa-globe", getattr(usinfo, "isActiveWeb", 0) in (1, "1", True)),
        ("fa-desktop", getattr(usinfo, "isActivePC", 0) in (1, "1", True)),
        ("fa-mobile", getattr(usinfo, "isActive", 0) in (1, "1", True)),
    ]

    icons = [FaLib.Glyph(k) for k, ok in flags if ok]
    icons = [x for x in icons if x]

    if icons:
        br = 22
        gap = 14
        totalw = len(icons) * (br * 2) + (len(icons) - 1) * gap
        startx = avx + coverSize // 2 - totalw // 2 + br
        cy = avy + coverSize + 34
        for i, ic in enumerate(icons):
            cx = startx + i * (br * 2 + gap)
            DrawIconBadge(bg, cx, cy, br, ic, iconfont)

    tx = pad + coverPad + coverSize + 52
    ty = pad + 68
    rightpad = 44
    maxw = (w - pad) - tx - rightpad

    nfit = FitText(d, name, namefont, maxw)
    DrawText(d, nfit, namefont, efont, tx, ty - 40, white)

    lineh = 50
    y0 = ty + 70
    for i, (label, value) in enumerate(infolines):
        y = y0 + i * lineh
        DrawText(d, f"{label}:", labelfont, efont, tx, y, dimgray)
        DrawText(d, FitText(d, str(value), valfont, maxw - 300), valfont, efont, tx + 300, y - 2, lightgray)

    outExt = (os.path.splitext(outpath)[1] or "").lower()
    if outExt in (".png", ".webp"):
        rgbPath = os.path.splitext(outpath)[0] + ".jpg"
    else:
        rgbPath = outpath

    rgb = FlattenRGBA(bg, (12, 12, 12))
    return SaveCard(rgb, rgbPath)

if __name__ == "__main__":
    userinfo = type("UserInfo", (object,), {
        "avatar": "https://zpsocial2-f8-org.zadn.vn/faf210ccd29530cb6984.jpg",
        "cover": "https://cover-talk.zadn.vn/2/8/d/b/16/83068eb61a79b0d8d430adeee5da5975.jpg",
        "zaloName": "Hạo Nguyên",
        "userId": 123456789,
        "gender": 0,
        "dob": 631152000,
        "lastActionTime": 1625097600000,
        "createdTs": 1577836800000,
        "bizPkg": {"pkgId": 1},
        "isActivePC": 1,
        "isActiveWeb": 1,
        "isActive": 1,
    })()

    out = os.path.join(os.getcwd(), "user_info_card.jpg")
    print(CreateUserInfoCard(out, userinfo))