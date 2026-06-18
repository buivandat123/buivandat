import subprocess
import os
import re
import base64
import random
import traceback
import requests
from datetime import datetime
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BANK_ALIASES = {
    "VCB": "VCB",
    "VIETCOM": "VCB",
    "VIETCOMBANK": "VCB",

    "VTB": "CTG",
    "VIETIN": "CTG",
    "VIETINBANK": "CTG",

    "BIDV": "BIDV",

    "AGRIBANK": "AGRIBANK",
    "AGRI": "AGRIBANK",

    "ACB": "ACB",

    "TPB": "TPB",
    "TPBANK": "TPB",

    "TCB": "TCB",
    "TECHCOM": "TCB",
    "TECHCOMBANK": "TCB",

    "VPB": "VPB",
    "VPBANK": "VPB",

    "MB": "MB",
    "MBBANK": "MB",

    "STB": "STB",
    "SACOMBANK": "STB",

    "MSB": "MSB",
    "VIB": "VIB",
    "VRB": "VRB",

    "OCB": "OCB",
    "SCB": "SCB",
    "SHB": "SHB",
    "HDB": "HDB",
    "HDBANK": "HDB",

    "EXIM": "EIB",
    "EXIMBANK": "EIB",

    "SEABANK": "SEABANK",
    "SEA_BANK": "SEABANK",

    "ABBANK": "ABBANK",
    "NCB": "NCB",

    "PVCOM": "PVCOMBANK",
    "PVCOMBANK": "PVCOMBANK",
    "PVCOM_BANK": "PVCOMBANK",

    "PUBLICBANK": "PUBLICBANK",
    "PUBLIC_BANK": "PUBLICBANK",

    "WOORI": "WOORI",
    "WOORIBANK": "WOORI",
    "WOORI_BANK": "WOORI",

    "CIMB": "CIMB",
    "HSBC": "HSBC",
    "TIMO": "TIMO",
    "CAKE": "CAKE",
    "UBANK": "UBANK",
}

CacheDir = Path("assets/cache")
CacheDir.mkdir(parents=True, exist_ok=True)

Theme = {
    "Radius": 28,
    "OuterPad": 60,
    "InnerPad": 40,
    "ShadowOpacity": 140,
    "ShadowBlur": 55,
    "ShadowOffset": 22,
    "CardStroke": (255, 255, 255, 55),
    "HeaderH": 90,
    "Text": (229, 231, 235, 255),
    "SubText": (203, 213, 225, 255),
    "Muted": (148, 163, 184, 255),
    "Dots": ["#ff5f56", "#ffbd2e", "#27c93f"],
}

Presets = [
    ("#0b1220", "#1b2a41"),
    ("#120c1c", "#2a1745"),
    ("#081a14", "#123b2d"),
    ("#140c18", "#2c143d"),
    ("#07131f", "#122840"),
]

_BanksCache = None


def LogError():
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] - ERROR OCCURRED:\n{traceback.format_exc()}\n{'-'*80}\n")


def _FontCandidates():
    c = []
    if os.name == "nt":
        wd = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        c += [
            wd / "JetBrainsMono-Regular.ttf",
            wd / "CascadiaMono.ttf",
            wd / "consola.ttf",
            wd / "SFMono-Regular.ttf",
            wd / "SFMono-Medium.ttf",
            wd / "SFMono-Semibold.ttf",
            wd / "SF Mono Regular.ttf",
        ]
    else:
        dirs = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local/share/fonts",
        ]
        names = [
            "JetBrainsMono-Regular.ttf",
            "CascadiaMono.ttf",
            "DejaVuSansMono.ttf",
            "DejaVuSansMono-Regular.ttf",
            "NotoSansMono-Regular.ttf",
            "LiberationMono-Regular.ttf",
            "UbuntuMono-R.ttf",
        ]
        for d in dirs:
            for n in names:
                c.append(d / n)
    return [p for p in c if p.exists() and p.is_file()]


def _FcMatchMono():
    try:
        out = subprocess.check_output(["fc-match", "-f", "%{file}\n", "monospace"], text=True).strip()
        p = Path(out)
        if p.exists():
            return p
    except:
        return None


def LoadFont(Size: int, Weight: str = "regular", FontPath: str | None = None):
    if FontPath:
        p = Path(FontPath)
        if p.exists():
            return ImageFont.truetype(str(p), Size)

    for p in _FontCandidates():
        try:
            return ImageFont.truetype(str(p), Size)
        except:
            pass

    p = _FcMatchMono()
    if p:
        try:
            return ImageFont.truetype(str(p), Size)
        except:
            pass

    return ImageFont.load_default()


def GenerateGradientImage(size, c1, c2):
    w, h = size
    base = Image.new("RGB", (w, h), c1)
    top = Image.new("RGB", (w, h), c2)
    mask = Image.new("L", (w, h))
    for y in range(h):
        v = int(255 * y / (h - 1 if h > 1 else 1))
        mask.paste(v, (0, y, w, y + 1))
    base.paste(top, (0, 0), mask)
    return base


def EnsureBgCache(size):
    for i, (c1, c2) in enumerate(Presets):
        p = CacheDir / f"background-Id{i}.png"
        if not p.exists():
            GenerateGradientImage(size, c1, c2).save(p, "PNG")


def ApplySonomaBackdrop(img):
    w, h = img.size
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    img = Image.alpha_composite(img, Image.new("RGBA", (w, h), (40, 80, 160, 25)))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((-w * 0.15, -h * 0.20, w * 0.55, h * 0.40), fill=(100, 200, 255, 40))
    g.ellipse((w * 0.45, -h * 0.15, w * 1.15, h * 0.55), fill=(180, 120, 255, 30))
    g.ellipse((w * 0.15, h * 0.60, w * 0.85, h * 1.20), fill=(80, 255, 220, 24))
    glow = glow.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.08)))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, Image.new("RGBA", (w, h), (0, 0, 0, 40)))
    noise = Image.effect_noise((w, h), 18).convert("L").point(lambda p: p * 0.18)
    grain = Image.merge("RGBA", (noise, noise, noise, noise))
    return Image.alpha_composite(img, grain)


def GetRandomBackground(w, h):
    EnsureBgCache((2600, 2600))
    files = list(CacheDir.glob("background-Id*.png"))
    if not files:
        return ApplySonomaBackdrop(GenerateGradientImage((w, h), "#0b0f14", "#141922").convert("RGBA"))
    img = Image.open(random.choice(files)).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    return ApplySonomaBackdrop(img)


def DrawShadow(base, pad, cw, ch):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    x0, y0 = pad, pad + Theme["ShadowOffset"]
    x1, y1 = pad + cw, pad + ch + Theme["ShadowOffset"]
    d.rounded_rectangle((x0, y0, x1, y1), radius=Theme["Radius"], fill=(0, 0, 0, Theme["ShadowOpacity"]))
    shadow = shadow.filter(ImageFilter.GaussianBlur(Theme["ShadowBlur"]))
    return Image.alpha_composite(base, shadow)


def DrawGlass(base, pad, cw, ch):
    w, h = base.size
    x0, y0 = pad, pad
    x1, y1 = x0 + cw, y0 + ch
    r = Theme["Radius"]
    hh = Theme["HeaderH"]

    blur = base.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.paste(blur, (x0, y0))

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y0, x1, y1), radius=r, fill=255)

    aBody = 18
    aHead = 24
    fade = 42

    glass = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=(255, 255, 255, aBody))

    headMask = Image.new("L", (cw, ch), 0)
    md = ImageDraw.Draw(headMask)
    md.rounded_rectangle((0, 0, cw, hh + r), radius=r, fill=255)
    md.rectangle((0, hh - r, cw, hh + fade), fill=255)
    for i in range(fade):
        v = int(255 * (1 - (i / (fade - 1 if fade > 1 else 1))))
        md.rectangle((0, hh + i, cw, hh + i + 1), fill=v)

    header = Image.new("RGBA", (cw, ch), (255, 255, 255, aHead))
    glass.paste(header, (x0, y0), headMask)

    layer = Image.composite(glass, layer, mask)

    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, outline=Theme["CardStroke"], width=1)

    hi = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(hi).rounded_rectangle((x0 + 1, y0 + 1, x1 - 1, y0 + hh + 12), radius=r, outline=(255, 255, 255, 28), width=1)
    layer = Image.alpha_composite(layer, hi)

    return Image.alpha_composite(base, layer), (x0, y0, x1, y1)


def DownBytes(url):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.content
    except:
        return b""


def QrImageFromDataUrl(dataUrl):
    b64 = re.sub(r"^data:image\/\w+;base64,", "", dataUrl or "")
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGBA")


def GetBanks():
    global _BanksCache
    if _BanksCache is not None:
        return _BanksCache
    try:
        r = requests.get("https://api.vietqr.io/v2/banks", timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        _BanksCache = r.json().get("data") or []
    except:
        _BanksCache = []
    return _BanksCache


def GetBankBin(code):
    c = str(code or "").upper()
    for b in GetBanks():
        if (b or {}).get("code") == c:
            return b.get("bin")
    return None


def FitText(draw, text, font, maxW):
    t = str(text or "")
    if not t:
        return ""
    while t and draw.textlength(t, font=font) > maxW:
        t = t[:-1]
    return t if t == text else (t[:-3] + "..." if len(t) > 3 else t)


def CircleCrop(im, size):
    im = im.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size, size), fill=255)
    im.putalpha(m)
    return im


def DrawBank(name, stk, stkName, bank, ndck, avaUrl, output, soTien):
    try:
        acqId = GetBankBin(bank)
        if not acqId:
            return None

        r = requests.post(
            "https://api.vietqr.io/v2/generate",
            headers={
                "x-client-id": "660d3755-30bb-461d-9bef-5e645a3dc6d3",
                "x-api-key": "03cd5d47-d8dd-43ee-adc6-daec670ab274",
                "User-Agent": "Mozilla/5.0",
            },
            data={
                "accountNo": str(stk),
                "accountName": str(stkName),
                "acqId": acqId,
                "addInfo": str(ndck),
                "amount": str(soTien),
                "template": "qr_only",
            },
            timeout=15,
        )
        r.raise_for_status()
        j = r.json()
        qrDataUrl = ((j.get("data") or {}).get("qrDataURL") or "")
        if not qrDataUrl:
            return None
        qrImg = QrImageFromDataUrl(qrDataUrl)

        ava = None
        avaBytes = DownBytes(avaUrl) if avaUrl else b""
        if avaBytes:
            try:
                ava = CircleCrop(Image.open(BytesIO(avaBytes)), 120)
            except:
                ava = None

        cw, ch = 980, 1080
        pad = Theme["OuterPad"]
        W, H = cw + pad * 2, ch + pad * 2

        img = GetRandomBackground(W, H)
        img = DrawShadow(img, pad, cw, ch)
        img, (x0, y0, x1, y1) = DrawGlass(img, pad, cw, ch)
        d = ImageDraw.Draw(img)

        hh = Theme["HeaderH"]
        for i, c in enumerate(Theme["Dots"]):
            dx = x0 + 42 + i * 36
            dy = y0 + hh // 2
            d.ellipse((dx - 10, dy - 10, dx + 10, dy + 10), fill=c)

        fTitle = LoadFont(34)
        fBig = LoadFont(40)
        fMd = LoadFont(28)
        fSm = LoadFont(24)

        d.text((x0 + cw // 2, y0 + hh // 2), "Payment code", fill=Theme["Text"], font=fTitle, anchor="mm")

        innerX = x0 + Theme["InnerPad"]
        innerY = y0 + hh + Theme["InnerPad"]
        innerW = cw - Theme["InnerPad"] * 2

        glow = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        bg_px = img.crop((innerX, innerY, innerX + 120, innerY + 120)).resize((1, 1)).getpixel((0, 0))
        r0, g0, b0, _ = bg_px
        gd.ellipse((0, 0, 360, 360), fill=(r0, g0, b0, 26))
        glow = glow.filter(ImageFilter.GaussianBlur(38))
        img.alpha_composite(glow, (innerX - 120, innerY - 120))

        if ava:
            img.alpha_composite(ava, (innerX, innerY))
            tx = innerX + 120 + 24
        else:
            tx = innerX
        ty = innerY + 6

        d = ImageDraw.Draw(img)
        d.text((tx, ty), FitText(d, str(name), fBig, innerW - (144 if ava else 0)), fill=Theme["Text"], font=fBig)
        d.text((tx, ty + 52), FitText(d, f"{str(bank).upper()}  {stk}", fMd, innerW - (144 if ava else 0)), fill=Theme["SubText"], font=fMd)
        d.text((tx, ty + 92), FitText(d, str(stkName), fSm, innerW - (144 if ava else 0)), fill=Theme["Muted"], font=fSm)

        chipW, chipH = 240, 56
        chipX = x1 - Theme["InnerPad"] - chipW
        chipY = innerY + 28
        chip = img.crop((chipX, chipY, chipX + chipW, chipY + chipH)).filter(ImageFilter.GaussianBlur(10))
        chipLayer = Image.new("RGBA", (chipW, chipH), (0, 0, 0, 0))
        chipLayer.paste(chip, (0, 0))
        cd = ImageDraw.Draw(chipLayer)
        cd.rounded_rectangle((0, 0, chipW, chipH), radius=18, fill=(255, 255, 255, 18), outline=(255, 255, 255, 55), width=1)
        img.alpha_composite(chipLayer, (chipX, chipY))
        d = ImageDraw.Draw(img)
        d.text((chipX + chipW // 2, chipY + chipH // 2), f"{soTien} VND", fill=Theme["Text"], font=fMd, anchor="mm")

        qrSize = 420
        qrX = x0 + (cw - qrSize) // 2
        qrY = innerY + 120 + 55

        panelW, panelH = qrSize + 54, qrSize + 54
        panelX = x0 + (cw - panelW) // 2
        panelY = qrY - 27

        panel = img.crop((panelX, panelY, panelX + panelW, panelY + panelH)).filter(ImageFilter.GaussianBlur(12))
        pLayer = Image.new("RGBA", (panelW, panelH), (0, 0, 0, 0))
        pLayer.paste(panel, (0, 0))
        pd = ImageDraw.Draw(pLayer)
        pd.rounded_rectangle((0, 0, panelW, panelH), radius=26, fill=(255, 255, 255, 14), outline=(255, 255, 255, 55), width=1)
        hi = Image.new("RGBA", (panelW, panelH), (0, 0, 0, 0))
        ImageDraw.Draw(hi).rounded_rectangle((1, 1, panelW - 1, 28), radius=26, outline=(255, 255, 255, 28), width=1)
        pLayer = Image.alpha_composite(pLayer, hi)
        img.alpha_composite(pLayer, (panelX, panelY))

        qr = qrImg.resize((qrSize, qrSize), Image.Resampling.LANCZOS)
        img.alpha_composite(qr, (qrX, qrY))

        d = ImageDraw.Draw(img)
        infoY = panelY + panelH + 34
        d.text((x0 + cw // 2, infoY), FitText(d, str(ndck), fMd, innerW), fill=Theme["SubText"], font=fMd, anchor="mm")
        d.text((x0 + cw // 2, infoY + 44), FitText(d, "Scan QR to pay", fSm, innerW), fill=Theme["Muted"], font=fSm, anchor="mm")

        outName = Path(str(output or "bank.png")).name
        fp = str(CacheDir / outName)
        img.convert("RGB").save(fp, optimize=True)
        return fp
    except:
        LogError()
        return None