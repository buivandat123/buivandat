from __future__ import annotations

import io
import random
import textwrap
from pathlib import Path
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer, guess_lexer
from pygments.token import Token

CacheDir = Path("assets/cache")
CacheDir.mkdir(parents=True, exist_ok=True)

CacheSize = (2600, 2600)

Theme = {
    "Bg": (18, 18, 22, 200),
    "HeaderBg": (22, 22, 26, 215),
    "ShadowOpacity": 140,
    "ShadowBlur": 60,
    "ShadowOffset": 30,
    "LineNumBg": (0, 0, 0, 0),
    "LineNumFg": "#6b7280",
    "TextFg": "#e5e7eb",
    "CardStroke": (255, 255, 255, 35),
    "Dots": ["#ff5f56", "#ffbd2e", "#27c93f"],
    "Radius": 22,
    "OuterPad": 80,
    "InnerPad": 44,
    "MaxWidth": 1800,
    "HeaderH": 78,
}


TokenColors = {
    Token.Keyword: "#c586c0",
    Token.Keyword.Constant: "#4fc1ff",
    Token.Keyword.Namespace: "#c586c0",
    Token.Name: "#9cdcfe",
    Token.Name.Function: "#dcdcaa",
    Token.Name.Class: "#4ec9b0",
    Token.String: "#ce9178",
    Token.Number: "#b5cea8",
    Token.Comment: "#6a9955",
    Token.Operator: "#d4d4d4",
    Token.Punctuation: "#d4d4d4",
    Token.Name.Decorator: "#c586c0",
}

Presets = [
    ("#0b1220", "#1b2a41"),   
    ("#120c1c", "#2a1745"),   
    ("#081a14", "#123b2d"),   
    ("#140c18", "#2c143d"),   
    ("#07131f", "#122840"),   
]



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


def GetTokenColor(TokenType):
    if TokenType in TokenColors:
        return TokenColors[TokenType]
    Parent = getattr(TokenType, "parent", None)
    return GetTokenColor(Parent) if Parent else Theme["TextFg"]


def GenerateGradientImage(Size, C1, C2):
    W, H = Size
    Base = Image.new("RGB", (W, H), C1)
    Top = Image.new("RGB", (W, H), C2)
    Mask = Image.new("L", (W, H))
    for y in range(H):
        v = int(255 * y / (H - 1 if H > 1 else 1))
        Mask.paste(v, (0, y, W, y + 1))
    Base.paste(Top, (0, 0), Mask)
    return Base


def EnsureCache():
    Existing = list(CacheDir.glob("background-Id*.png"))
    if len(Existing) >= len(Presets):
        return
    for i, (C1, C2) in enumerate(Presets):
        P = CacheDir / f"background-Id{i}.png"
        if not P.exists():
            GenerateGradientImage(CacheSize, C1, C2).save(P, "PNG")


def ApplySonomaBackdrop(Img: Image.Image):
    W, H = Img.size

    Img = Img.filter(ImageFilter.GaussianBlur(1.0))

    Tint = Image.new("RGBA", (W, H), (40, 80, 160, 25))
    Img = Image.alpha_composite(Img, Tint)

    Glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    G = ImageDraw.Draw(Glow)

    G.ellipse((-W * 0.15, -H * 0.20, W * 0.55, H * 0.40), fill=(100, 200, 255, 40))
    G.ellipse((W * 0.45, -H * 0.15, W * 1.15, H * 0.55), fill=(180, 120, 255, 30))
    G.ellipse((W * 0.15, H * 0.60, W * 0.85, H * 1.20), fill=(80, 255, 220, 24))

    Glow = Glow.filter(ImageFilter.GaussianBlur(int(min(W, H) * 0.08)))
    Img = Image.alpha_composite(Img, Glow)

    Dim = Image.new("RGBA", (W, H), (0, 0, 0, 40))
    Img = Image.alpha_composite(Img, Dim)

    Noise = Image.effect_noise((W, H), 18).convert("L")
    Noise = Noise.point(lambda p: p * 0.18)
    Grain = Image.merge("RGBA", (Noise, Noise, Noise, Noise))
    Img = Image.alpha_composite(Img, Grain)

    return Img

def GetRandomBackground(W: int, H: int):
    EnsureCache()
    Files = list(CacheDir.glob("background-Id*.png"))
    if not Files:
        Img = GenerateGradientImage((W, H), "#0b0f14", "#141922").convert("RGBA")
        return ApplySonomaBackdrop(Img)
    Img = Image.open(random.choice(Files)).convert("RGBA")
    Img = Img.resize((W, H), Image.Resampling.LANCZOS)
    return ApplySonomaBackdrop(Img)


def WrapCode(Code: str, CharW: float):
    MaxW = Theme["MaxWidth"] - 80 - (Theme["InnerPad"] * 2)
    Cpl = int(MaxW / (CharW if CharW > 0 else 10))
    if Cpl < 20:
        Cpl = 20
    Wp = textwrap.TextWrapper(width=Cpl, expand_tabs=False, replace_whitespace=False, drop_whitespace=False)
    Lines = (Code or "").splitlines() or [" "]
    Out = []
    for L in Lines:
        Out.extend(Wp.wrap(L) if len(L) > Cpl else [L])
    return Out, "\n".join(Out), Cpl


def BuildLayout(WrappedLines, CharW: float, LineH: int):
    MaxLen = max((len(x) for x in WrappedLines), default=1)
    CalcW = int(Theme["InnerPad"] + 80 + (MaxLen * CharW) + Theme["InnerPad"])
    CardW = max(800, min(CalcW, Theme["MaxWidth"]))
    CardH = Theme["HeaderH"] + (len(WrappedLines) * LineH) + Theme["InnerPad"]
    Pad = Theme["OuterPad"]
    FullW = CardW + (Pad * 2)
    FullH = CardH + (Pad * 2)
    return CardW, CardH, FullW, FullH


def DrawShadow(BaseImg, Pad, CardW, CardH):
    Shadow = Image.new("RGBA", BaseImg.size, (0, 0, 0, 0))
    D = ImageDraw.Draw(Shadow)
    X0, Y0 = Pad, Pad + Theme["ShadowOffset"]
    X1, Y1 = Pad + CardW, Pad + CardH + Theme["ShadowOffset"]
    D.rounded_rectangle((X0, Y0, X1, Y1), radius=Theme["Radius"], fill=(0, 0, 0, Theme["ShadowOpacity"]))
    Shadow = Shadow.filter(ImageFilter.GaussianBlur(Theme["ShadowBlur"]))
    return Image.alpha_composite(BaseImg, Shadow)


def DrawGlass(base, backdrop, pad, cw, ch):
    w, h = base.size
    x0, y0 = pad, pad
    x1, y1 = x0 + cw, y0 + ch
    r = Theme["Radius"]
    hh = Theme["HeaderH"]

    blur = backdrop.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14))
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

def RenderCodeToBytes(Code: str, Title: str = "Snippet") -> tuple[bytes, int, int]:
    FontSize = 28
    FontCode = LoadFont(FontSize, "regular")
    FontUi = LoadFont(30, "regular")

    Dummy = Image.new("RGBA", (10, 10))
    DummyDraw = ImageDraw.Draw(Dummy)
    CharW = DummyDraw.textlength("A", font=FontCode)
    LineH = int(FontSize * 1.55)

    WrappedLines, Processed, _ = WrapCode(Code, CharW)
    CardW, CardH, FullW, FullH = BuildLayout(WrappedLines, CharW, LineH)

    Backdrop = GetRandomBackground(FullW, FullH)
    Img = Backdrop.copy()
    Pad = Theme["OuterPad"]

    Img = DrawShadow(Img, Pad, CardW, CardH)
    Img, (X0, Y0, X1, Y1) = DrawGlass(Img, Backdrop, Pad, CardW, CardH)

    D = ImageDraw.Draw(Img)

    HH = Theme["HeaderH"]
    for i, C in enumerate(Theme["Dots"]):
        Dx = X0 + 35 + (i * 35)
        Dy = Y0 + HH // 2
        D.ellipse((Dx - 10, Dy - 10, Dx + 10, Dy + 10), fill=C)

    D.text((X0 + CardW // 2, Y0 + HH // 2), Title, fill=Theme["TextFg"], font=FontUi, anchor="mm")

    try:
        Lexer = guess_lexer(Processed)
    except:
        Lexer = PythonLexer()

    Tokens = list(lex(Processed, Lexer))

    StartX = X0 + Theme["InnerPad"] + 80
    CurrX = StartX
    CurrY = Y0 + HH + 26
    LineIdx = 1

    D.text((X0 + Theme["InnerPad"], CurrY), str(LineIdx), fill=Theme["LineNumFg"], font=FontCode)

    for Tt, Val in Tokens:
        Parts = Val.split("\n")
        for i, Part in enumerate(Parts):
            if Part:
                PartW = DummyDraw.textlength(Part, font=FontCode)
                if CurrX + PartW > X1 + 10:
                    CurrX = StartX
                    CurrY += LineH
                D.text((CurrX, CurrY), Part, fill=GetTokenColor(Tt), font=FontCode)
                CurrX += PartW
            if i < len(Parts) - 1:
                CurrX = StartX
                CurrY += LineH
                LineIdx += 1
                if LineIdx <= len(WrappedLines):
                    D.text((X0 + Theme["InnerPad"], CurrY), str(LineIdx), fill=Theme["LineNumFg"], font=FontCode)

    Buf = io.BytesIO()
    Img.save(Buf, format="PNG", optimize=True)
    return Buf.getvalue(), FullW, FullH