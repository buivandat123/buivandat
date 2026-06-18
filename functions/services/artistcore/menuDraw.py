from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, os

from .font.fontLibs import *

w_canvas = 2048
pad = 96
r_card = 18

cols = 4
rows = 3
max_items = cols * rows

bg_top = (16, 20, 32)
bg_bot = (10, 12, 20)

g_bg = (255, 255, 255, 26)
g_border = (255, 255, 255, 90)
g_inner = (255, 255, 255, 45)

c_text = (246, 248, 255)
c_sub = (175, 182, 205)

BaseDir = Path(__file__).resolve().parent

FONT_REG = "Zen-dots.ttf"
FONT_BOLD = "Milker-Bold.otf"

perm_map = {
    4: ("ROOT", (255, 90, 90)),
    3: ("HIGH ADMIN", (255, 90, 90)),
    2: ("BOT ADMIN", (255, 190, 120)),
    1: ("GROUP ADMIN", (130, 220, 170)),
    0: ("USER", (130, 180, 255))
}

def font(sz, bold=False):
    return FontLib.Load(FONT_BOLD if bold else FONT_REG, sz)

def gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line(
            (0, y, w, y),
            fill=(
                int(bg_top[0] * (1 - t) + bg_bot[0] * t),
                int(bg_top[1] * (1 - t) + bg_bot[1] * t),
                int(bg_top[2] * (1 - t) + bg_bot[2] * t),
            )
        )
    return img.convert("RGBA")

def blobs(base):
    w, h = base.size
    layer = Image.new("RGBA", base.size)
    d = ImageDraw.Draw(layer)
    for _ in range(7):
        r = random.randint(400, 700)
        x = random.randint(-200, w)
        y = random.randint(-200, h)
        d.ellipse(
            (x, y, x + r, y + r),
            fill=random.choice([
                (120, 170, 255, 60),
                (190, 120, 255, 55),
                (120, 255, 200, 50)
            ])
        )
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(140)))

def noise(base):
    w, h = base.size
    n = Image.new("L", (w, h))
    px = n.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(120, 136)
    base.alpha_composite(
        Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 18)))
    )

def glass(canvas, box):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    blur = canvas.crop(box).filter(ImageFilter.GaussianBlur(26))
    layer = Image.alpha_composite(blur, Image.new("RGBA", (w, h), g_bg))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), r_card, fill=255)
    canvas.paste(layer, box, mask)

def badge(d, canvas, x, y, text, color):
    f = font(22, True)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    tw = r - l
    th = b - t
    px = 24
    py = 18
    bw = tw + px * 2
    bh = th + py
    box = (x, y, x + bw, y + bh)
    glass(canvas, box)
    d.text((x + px, y + (bh - th) // 2 - 1), text, font=f, fill=color)
    return bw, bh

def trim_text(d, text, font_, max_width):
    text = str(text or "").strip()
    if not text:
        return ""
    while text and d.textbbox((0, 0), text, font=font_)[2] > max_width:
        text = text[:-2].rstrip() + "…"
    return text

def draw_menu(title, cmds, out_path, page=1, total_page=1):
    items = cmds[:max_items]
    h_card = 260
    gap = 48
    h_canvas = pad * 2 + 240 + rows * (h_card + gap)
    img = gradient(w_canvas, h_canvas)
    blobs(img)
    noise(img)
    d = ImageDraw.Draw(img)

    f = font(100, True)
    l, t, r, b = d.textbbox((0, 0), title, font=f)
    tw = r - l

    d.text(((w_canvas - tw) // 2, 56), title, font=f, fill=c_text)

    y0 = 220
    w_card = (w_canvas - pad * 2 - gap * (cols - 1)) // cols

    for i, it in enumerate(items):
        c = i % cols
        r = i // cols
        x1 = pad + c * (w_card + gap)
        y1 = y0 + r * (h_card + gap)
        x2 = x1 + w_card
        y2 = y1 + h_card

        glass(img, (x1, y1, x2, y2))

        name_font = font(34, True)
        desc_font = font(24)

        name = trim_text(d, it.get("name", ""), name_font, w_card - 80)
        desc = trim_text(d, it.get("description", ""), desc_font, w_card - 80)

        d.text((x1 + 40, y1 + 32), name, font=name_font, fill=c_text)
        d.text((x1 + 40, y1 + 78), desc, font=desc_font, fill=c_sub)

        pt, pc = perm_map.get(int(it.get("permission", 0) or 0), perm_map[0])
        pt, pc = perm_map.get(int(it.get("permission", 0) or 0), perm_map[0])

        f = font(22, True)
        l, t, r, b = d.textbbox((0, 0), pt, font=f)
        tw = r - l
        th = b - t
        p = 24
        bw = tw + p * 2

        badge(d, img, x2 - bw - 20, y2 - 59, pt, pc)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return img.size