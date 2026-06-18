# -*- coding: utf-8 -*-

import os
import time
import platform
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from zlapi.models import Message

des = {
    "version": "1.0.0",
    "credits": "bé tiên cute",
    "description": "Check bot (ảnh 100%)",
    "power": "Thành viên"
}

CACHE_DIR = "modules/cache/check"
FONT_BOLD = "modules/cache/font/BeVietnamPro-Bold.ttf"
FONT_REG = "modules/cache/font/BeVietnamPro-Regular.ttf"
os.makedirs(CACHE_DIR, exist_ok=True)

W, H = 1600, 760
BOT_START_TIME = time.time()

COOLDOWN = 15
_last_used = {}

BG1 = (8, 12, 20)
BG2 = (14, 18, 28)

TXT = (245, 248, 255, 235)
SUB = (175, 190, 210, 215)

PANEL = (16, 20, 30, 185)
PANEL2 = (14, 18, 28, 175)
STROKE = (140, 170, 220, 55)

ACC_A = (90, 210, 255)
ACC_B = (255, 140, 220)
ACC_C = (255, 210, 90)

def _font(path, size):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def f_b(size):
    return _font(FONT_BOLD, size)

def f_r(size):
    return _font(FONT_REG, size) if os.path.exists(FONT_REG) else _font(FONT_BOLD, size)

def _rounded(draw, box, r, fill=None, outline=None, width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def _draw_bg():
    base = Image.new("RGB", (W, H), BG1)
    d = ImageDraw.Draw(base)

    for y in range(H):
        t = y / max(1, H - 1)
        r = int(BG1[0] * (1 - t) + BG2[0] * t)
        g = int(BG1[1] * (1 - t) + BG2[1] * t)
        b = int(BG1[2] * (1 - t) + BG2[2] * t)
        d.line((0, y, W, y), fill=(r, g, b))

    base = base.convert("RGBA")

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid, "RGBA")
    step = 80
    for x in range(0, W, step):
        gd.line((x, 0, x, H), fill=(120, 160, 220, 16))
    for y in range(0, H, step):
        gd.line((0, y, W, y), fill=(120, 160, 220, 16))
    base = Image.alpha_composite(base, grid)

    vign = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-W * 0.2, -H * 0.8, W * 1.2, H * 1.5), fill=240)
    vign = vign.filter(ImageFilter.GaussianBlur(int(min(W, H) * 0.08)))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    base = Image.composite(base, dark, vign).convert("RGBA")

    return base

def _glass_panel(base, box, r=28, fill=PANEL, stroke=STROKE, glow=(90, 210, 255, 70)):
    x0, y0, x1, y1 = map(int, box)

    crop = base.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(10))
    base.paste(crop, (x0, y0))

    glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer, "RGBA")
    _rounded(gd, (x0, y0, x1, y1), r, fill=None, outline=glow, width=10)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(14))
    base = Image.alpha_composite(base, glow_layer)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")
    _rounded(od, (x0, y0, x1, y1), r, fill=fill, outline=stroke, width=2)
    base = Image.alpha_composite(base, overlay)
    return base

def _fmt_uptime(sec):
    sec = int(max(0, sec))
    d = sec // 86400
    sec %= 86400
    h = sec // 3600
    sec %= 3600
    m = sec // 60
    s = sec % 60
    if d > 0:
        return f"{d}d {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"

def build_check_image(prefix, uptime, ping_ms, thread_id, author_id):
    base = _draw_bg()
    draw = ImageDraw.Draw(base, "RGBA")

    outer = (50, 50, W - 50, H - 50)
    base = _glass_panel(base, outer, r=36, fill=PANEL, stroke=STROKE, glow=(ACC_A[0], ACC_A[1], ACC_A[2], 60))

    header = (85, 85, W - 85, 220)
    base = _glass_panel(base, header, r=28, fill=PANEL2, stroke=STROKE, glow=(ACC_B[0], ACC_B[1], ACC_B[2], 55))

    draw = ImageDraw.Draw(base, "RGBA")
    draw.text((130, 120), "SYSTEM CHECK", font=f_b(62), fill=TXT)
    draw.text((130, 180), datetime.now().strftime("%d/%m/%Y • %H:%M:%S"), font=f_r(26), fill=SUB)

    pill = (W - 430, 120, W - 160, 185)
    _rounded(draw, pill, 20, fill=(12, 16, 24, 210), outline=(ACC_C[0], ACC_C[1], ACC_C[2], 210), width=3)
    draw.text(((pill[0] + pill[2]) / 2, (pill[1] + pill[3]) / 2),
              f"Ping: {ping_ms:.0f} ms", font=f_b(30),
              fill=(ACC_C[0], ACC_C[1], ACC_C[2], 235), anchor="mm")

    body = (85, 250, W - 85, H - 85)
    base = _glass_panel(base, body, r=28, fill=PANEL2, stroke=STROKE, glow=(ACC_A[0], ACC_A[1], ACC_A[2], 35))
    draw = ImageDraw.Draw(base, "RGBA")

    x = 140
    y = 300
    line_gap = 62

    items = [
        ("Prefix", str(prefix)),
        ("Uptime", uptime),
        ("Platform", platform.system() + " " + platform.release()),
        ("Python", platform.python_version()),
        ("Thread ID", str(thread_id)),
        ("User ID", str(author_id)),
    ]

    for i, (k, v) in enumerate(items):
        color = (ACC_A[0], ACC_A[1], ACC_A[2], 235) if i % 2 == 0 else (ACC_B[0], ACC_B[1], ACC_B[2], 235)
        draw.text((x, y), f"• {k}:", font=f_b(34), fill=color)
        draw.text((x + 240, y), str(v), font=f_r(34), fill=TXT)
        y += line_gap

    draw.text((130, H - 120), "Powered by bé tiên cute", font=f_r(26), fill=(190, 205, 220, 190))
    draw.text((130, H - 85), f"Command: {prefix}check", font=f_r(26), fill=(190, 205, 220, 190))

    return base.convert("RGB")

def _save_img(img):
    path = os.path.join(CACHE_DIR, f"check_{int(time.time()*1000)}.jpg")
    img.save(path, "JPEG", quality=95, optimize=True)
    return path

def _send_image(client, img, thread_id, thread_type, ttl=120000):
    path = _save_img(img)
    try:
        client.sendLocalImage(
            path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=img.size[0],
            height=img.size[1],
            ttl=ttl
        )
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

def check_cmd(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    now = time.time()

    last = _last_used.get(str(author_id), 0)
    if now - last < COOLDOWN:
        return
    _last_used[str(author_id)] = now

    t0 = time.time()
    ping_ms = (time.time() - t0) * 1000.0

    uptime = _fmt_uptime(time.time() - BOT_START_TIME)

    img = build_check_image(prefix, uptime, ping_ms, thread_id, author_id)
    _send_image(client, img, thread_id, thread_type, ttl=120000)

def LIGHT():
    return {
        "check": check_cmd,
        "chk": check_cmd
    }