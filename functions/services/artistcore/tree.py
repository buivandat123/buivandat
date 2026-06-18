from __future__ import annotations

import io
import os
import random
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
    "Dots": ["#ff5f56", "#ffbd2e", "#27c93f"],
    "Radius": 22,
    "OuterPad": 80,
    "InnerPad": 44,
    "MaxWidth": 1800,
    "HeaderH": 78,
}

TreeColors = {
    "Prefix": "#6b7280",
    "Dir": "#4ec9b0",
    "File": "#e5e7eb",
    "Caret": (210, 210, 220, 210),
    "IconDir": (78, 201, 176, 220),
    "IconFile": (165, 180, 252, 220),
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
    return Image.alpha_composite(Img, Grain)


def GetRandomBackground(W: int, H: int):
    EnsureCache()
    Files = list(CacheDir.glob("background-Id*.png"))
    if not Files:
        Img = GenerateGradientImage((W, H), "#0b0f14", "#141922").convert("RGBA")
        return ApplySonomaBackdrop(Img)
    Img = Image.open(random.choice(Files)).convert("RGBA")
    Img = Img.resize((W, H), Image.Resampling.LANCZOS)
    return ApplySonomaBackdrop(Img)


def DrawShadow(BaseImg, Pad, CardW, CardH):
    Shadow = Image.new("RGBA", BaseImg.size, (0, 0, 0, 0))
    D = ImageDraw.Draw(Shadow)
    X0, Y0 = Pad, Pad + Theme["ShadowOffset"]
    X1, Y1 = Pad + CardW, Pad + CardH + Theme["ShadowOffset"]
    D.rounded_rectangle((X0, Y0, X1, Y1), radius=Theme["Radius"], fill=(0, 0, 0, Theme["ShadowOpacity"]))
    Shadow = Shadow.filter(ImageFilter.GaussianBlur(Theme["ShadowBlur"]))
    return Image.alpha_composite(BaseImg, Shadow)


def DrawGlass(BaseImg, Pad, CardW, CardH):
    W, H = BaseImg.size
    X0, Y0 = Pad, Pad
    X1, Y1 = X0 + CardW, Y0 + CardH
    R = Theme["Radius"]
    HH = Theme["HeaderH"]
    BlurLayer = BaseImg.crop((X0, Y0, X1, Y1)).filter(ImageFilter.GaussianBlur(14))
    Layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Layer.paste(BlurLayer, (X0, Y0))
    D = ImageDraw.Draw(Layer)
    D.rounded_rectangle((X0, Y0, X1, Y1), radius=R, fill=Theme["Bg"])
    D.rounded_rectangle((X0, Y0, X1, Y0 + HH + R), radius=R, fill=Theme["HeaderBg"])
    D.rectangle((X0, Y0 + HH - R, X1, Y0 + HH + R), fill=Theme["HeaderBg"])
    D.rectangle((X0, Y0 + HH, X1, Y0 + HH + R), fill=Theme["Bg"])
    D.rounded_rectangle((X0, Y0, X1, Y1), radius=R, outline=(255, 255, 255, 55), width=1)
    Hi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Hd = ImageDraw.Draw(Hi)
    Hd.rounded_rectangle((X0 + 1, Y0 + 1, X1 - 1, Y0 + HH + 10), radius=R, outline=(255, 255, 255, 28), width=1)
    Layer = Image.alpha_composite(Layer, Hi)
    return Image.alpha_composite(BaseImg, Layer), (X0, Y0, X1, Y1)


def _ListDir(p: Path):
    try:
        items = list(p.iterdir())
    except:
        return []
    items.sort(key=lambda x: (0 if x.is_dir() else 1, x.name.lower()))
    return items


def BuildTreeLines(Root: Path, MaxDepth: int = 6, MaxItems: int = 500):
    Root = Path(Root)
    Out = []
    Cnt = 0

    def Walk(p: Path, Depth: int, PrefixParts: list[bool]):
        nonlocal Cnt
        if Depth > MaxDepth or Cnt >= MaxItems:
            return
        items = _ListDir(p)
        for i, it in enumerate(items):
            if Cnt >= MaxItems:
                return
            last = i == len(items) - 1
            pref = "".join(("│   " if hasNext else "    ") for hasNext in PrefixParts)
            branch = "└── " if last else "├── "
            Out.append((pref + branch, it.name, it.is_dir(), Depth))
            Cnt += 1
            if it.is_dir():
                Walk(it, Depth + 1, PrefixParts + [not last])

    Out.append(("", Root.name if Root.name else str(Root), True, 0))
    Walk(Root, 1, [])
    return Out


def _TrimToWidth(Draw: ImageDraw.ImageDraw, Text: str, Font: ImageFont.FreeTypeFont, MaxW: float):
    if Draw.textlength(Text, font=Font) <= MaxW:
        return Text
    ell = "…"
    if Draw.textlength(ell, font=Font) > MaxW:
        return ""
    lo, hi = 0, len(Text)
    while lo < hi:
        mid = (lo + hi) // 2
        s = Text[:mid] + ell
        if Draw.textlength(s, font=Font) <= MaxW:
            lo = mid + 1
        else:
            hi = mid
    return Text[: max(0, lo - 1)] + ell


def RenderTreeToBytes(Root: str | Path, Title: str = "Explorer", MaxDepth: int = 6, MaxItems: int = 500) -> tuple[bytes, int, int]:
    FontSize = 28
    FontCode = LoadFont(FontSize, "regular")
    FontUi = LoadFont(30, "regular")

    Dummy = Image.new("RGBA", (10, 10))
    DummyDraw = ImageDraw.Draw(Dummy)
    LineH = int(FontSize * 1.55)

    Lines = BuildTreeLines(Path(Root), MaxDepth=MaxDepth, MaxItems=MaxItems)
    MaxLen = 1
    for pref, name, isDir, depth in Lines:
        s = (pref + ("▸ " if isDir and depth > 0 else "  ") + name) if depth > 0 else name
        MaxLen = max(MaxLen, len(s))

    CharW = DummyDraw.textlength("A", font=FontCode)
    CalcW = int(Theme["InnerPad"] * 2 + (MaxLen * CharW) + 80)
    CardW = max(900, min(CalcW, Theme["MaxWidth"]))
    CardH = Theme["HeaderH"] + (len(Lines) * LineH) + Theme["InnerPad"] + 22
    Pad = Theme["OuterPad"]
    FullW = CardW + (Pad * 2)
    FullH = CardH + (Pad * 2)

    Img = GetRandomBackground(FullW, FullH)
    Img = DrawShadow(Img, Pad, CardW, CardH)
    Img, (X0, Y0, X1, Y1) = DrawGlass(Img, Pad, CardW, CardH)

    D = ImageDraw.Draw(Img)
    HH = Theme["HeaderH"]

    for i, C in enumerate(Theme["Dots"]):
        Dx = X0 + 35 + (i * 35)
        Dy = Y0 + HH // 2
        D.ellipse((Dx - 10, Dy - 10, Dx + 10, Dy + 10), fill=C)

    D.text((X0 + CardW // 2, Y0 + HH // 2), Title, fill=Theme["TextFg"], font=FontUi, anchor="mm")

    StartX = X0 + Theme["InnerPad"]
    CurrY = Y0 + HH + 26
    MaxTextW = (X1 - StartX) - 16

    def DrawCaret(x, y, size=10):
        p = [(x, y - size), (x, y + size), (x + int(size * 1.35), y)]
        D.polygon(p, fill=TreeColors["Caret"])

    def DrawIcon(x, y, isDir):
        r = 6
        w, h = 16, 14
        fill = TreeColors["IconDir"] if isDir else TreeColors["IconFile"]
        D.rounded_rectangle((x, y - h // 2, x + w, y + h // 2), radius=r, fill=fill)

    for idx, (pref, name, isDir, depth) in enumerate(Lines):
        x = StartX
        y = CurrY + idx * LineH

        if depth == 0:
            DrawIcon(x, y + 10, True)
            tx = x + 24
            nm = _TrimToWidth(DummyDraw, name, FontCode, MaxTextW - 24)
            D.text((tx, y), nm, fill=TreeColors["Dir"], font=FontCode)
            continue

        DrawCaret(x + 2, y + 10, 8) if isDir else None
        DrawIcon(x + 18, y + 10, isDir)

        tx = x + 44
        prefW = DummyDraw.textlength(pref, font=FontCode)
        nmMax = MaxTextW - (44 + prefW)
        nm = _TrimToWidth(DummyDraw, name, FontCode, nmMax)

        D.text((tx, y), pref, fill=TreeColors["Prefix"], font=FontCode)
        D.text((tx + prefW, y), nm, fill=(TreeColors["Dir"] if isDir else TreeColors["File"]), font=FontCode)

    Buf = io.BytesIO()
    Img.save(Buf, format="PNG", optimize=True)
    return Buf.getvalue(), FullW, FullH


IgnoreNames = {
    ".git", "__pycache__", "node_modules", ".idea", ".vscode",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build"
}

IgnoreExt = {".pyc", ".pyo", ".log", ".tmp", ".cache"}

def _ListDir(p: Path):
    try:
        items = []
        for x in p.iterdir():
            n = x.name
            if n in IgnoreNames or n.startswith("."):
                continue
            if x.is_file() and x.suffix.lower() in IgnoreExt:
                continue
            items.append(x)
    except:
        return []
    items.sort(key=lambda x: (0 if x.is_dir() else 1, x.name.lower()))
    return items

if __name__ == "__main__":
    from pathlib import Path
    Root = Path(r"D:/Nguyen Coder/Codespace/Python/Project/@bug-zalo")
    PngBytes, W, H = RenderTreeToBytes(Root, Title=f"Explorer - {Root.name}", MaxDepth=6, MaxItems=400)
    Out = Path("tree.png")
    Out.write_bytes(PngBytes)
    print("OK:", Out.resolve(), W, H)