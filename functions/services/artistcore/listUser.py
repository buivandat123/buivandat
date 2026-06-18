from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

import os, random, requests, re
from functools import lru_cache

from .font.fontLibs import *

W = 1536
H = 768
PAD = 48

BgTop = (14, 18, 32)
BgBot = (6, 8, 16)

GlassFill = (255, 255, 255, 34)

TextTitle = (246, 248, 255, 255)
TextSub = (188, 196, 220, 255)
TextDim = (150, 158, 186, 255)

FontRegName = "arial.ttf"
FontBoldName = "Darley-sans.otf"
FontMilkerName = "Darley-sans.otf"

def Font(Size, Bold=False, Milker=False):
    if Milker:
        return FontLib.Load(FontMilkerName, Size)
    if Bold:
        return FontLib.Load(FontBoldName, Size)
    return FontLib.Load(FontRegName, Size)

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
    BlurImg = Img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(24)).convert("RGBA")
    Layer = Image.alpha_composite(BlurImg, Image.new("RGBA", (bw, bh), GlassFill))
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

def DrawList(*, Owner, Admins, OutPath, Title="Admins", SubTitle="", Source="Group", ItemsPerPage=10):
    Owner = Owner or {}
    Admins = [x for x in list(Admins or []) if isinstance(x, dict)]

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

    Pick = Owner
    BigThumb = 320
    BigR = 44
    ThumbX = int(Lx1 + (LeftW - BigThumb) / 2)
    ThumbY = int(Ly1 + 28)

    Avatar = LoadImage((Pick.get("avatar") or Pick.get("avatarUrl") or Pick.get("thumb") or ""), (BigThumb, BigThumb))
    BigMask = RoundMask(BigThumb, BigThumb, BigR)
    Img.paste(Avatar, (ThumbX, ThumbY), BigMask)

    TitleFont = Font(40, Bold=True)
    SubFont = Font(26)
    BadgeFont = Font(26, Milker=True)

    BigName = FitText(D, Pick.get("name", "Unknown"), TitleFont, LeftW - 52)
    BigRole = FitText(D, Pick.get("role", "Owner"), SubFont, LeftW - 52)

    Tx = Lx1 + 26
    Ty = ThumbY + BigThumb + 22
    D.text((Tx, Ty), BigName, font=TitleFont, fill=TextTitle)
    D.text((Tx, Ty + 52), BigRole, font=SubFont, fill=TextSub)

    BadgeText = str(Source or "Group")
    Bw = int(D.textlength(BadgeText, font=BadgeFont) + 72)
    Bh = 56
    Bx1 = int(Lx1 + (LeftW - Bw) / 2)
    By1 = int(Ly2 - 26 - Bh)
    Glass(Img, (Bx1, By1, Bx1 + Bw, By1 + Bh), 28)
    D.text((Bx1 + 36, By1 + 14), BadgeText, font=BadgeFont, fill=(255, 255, 255, 245))

    Items = Admins[:int(ItemsPerPage or 10)]
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

    for i, A in enumerate(Items):
        c = i // Rows
        r = i % Rows

        x1 = int(Rx1 + 18 + c * (ColW + CGap))
        y1 = int(Ry1 + 18 + r * (RowH + RGap))
        x2 = int(x1 + ColW)
        y2 = int(y1 + RowH)

        Glass(Img, (x1, y1, x2, y2), 26)

        ix = x1 + 20
        iy = int(y1 + (RowH - Thumb) / 2)

        Av = LoadImage((A.get("avatar") or A.get("avatarUrl") or A.get("thumb") or ""), (Thumb, Thumb))
        Img.paste(Av, (ix, iy), ThumbMask)

        Tx2 = ix + Thumb + 18
        MaxTextW = x2 - Tx2 - 20

        NameStr = FitText(D, A.get("name", "Unknown"), RowTitleFont, MaxTextW)

        role = str(A.get("role") or "Admin")
        uid = str(A.get("uid") or A.get("userId") or "")
        meta = role if not uid else f"{role}"
        MetaStr = FitText(D, meta, RowMetaFont, MaxTextW)

        D.text((Tx2, y1 + 18), NameStr, font=RowTitleFont, fill=TextTitle)
        D.text((Tx2, y1 + 18 + 46), MetaStr, font=RowMetaFont, fill=TextSub)

        Idx = str(i + 1)
        iw = int(D.textlength(Idx, font=IdxFont))
        D.text((x2 - 16 - iw, y2 - 14 - 24), Idx, font=IdxFont, fill=TextDim)

    if Title or SubTitle:
        HeadFont = Font(34, Bold=True)
        SubHeadFont = Font(22)
        hx = Rx1 + 18
        hy = Ly1 + 6
        if Title:
            D.text((hx, hy), FitText(D, Title, HeadFont, Rx2 - hx - 18), font=HeadFont, fill=(255, 255, 255, 210))
        if SubTitle:
            D.text((hx, hy + 44), FitText(D, SubTitle, SubHeadFont, Rx2 - hx - 18), font=SubHeadFont, fill=(188, 196, 220, 200))

    os.makedirs(os.path.dirname(OutPath), exist_ok=True)
    Img.save(OutPath, "PNG")
    return OutPath, W, H