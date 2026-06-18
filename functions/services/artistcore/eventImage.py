from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import os, random, requests
from io import BytesIO

from functions.services.artistcore.font.fontLibs import *

w = 1600
h = 600
pad = 64
r = 36

bg_top = (14, 18, 30)
bg_bot = (8, 10, 18)

g_bg = (255, 255, 255, 28)

c_title = (245, 248, 255)
c_artist = (180, 190, 215)
c_time = (150, 160, 190)

font_reg = "Darley-sans.otf"
font_bold = "Dela-gothic-one.ttf"
font_milker = "Milker-Bold.otf"

def font(size, bold=False, milker=False):
    name = font_milker if milker else (font_bold if bold else font_reg)
    return FontLib.Load(name, size)

def fit_text(draw, text, font_obj, max_width):
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

def gradient(w0, h0):
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

def blobs(img):
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

def noise(img):
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

def glass(canvas, box, radius=r, alpha=g_bg, blur=26, aa=4, pill=False):
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

def load_image(url, size=(500, 500)):
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
        import re
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
        except Exception:
            continue

    return blank()

def media_dir():
    return Path(__file__).resolve().parent / "media"

def load_icon(name, size):
    if name and isinstance(name, str):
        p = (media_dir() / name)
        try:
            if p.is_file():
                return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
        except Exception:
            pass

    p = media_dir() / "noIcon.png"
    try:
        if p.is_file():
            return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
    except Exception:
        pass

    return None

def circle_mask(size, aa=6):
    s = size * aa
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((0, 0, s - 1, s - 1), fill=255)
    return m.resize((size, size), Image.LANCZOS)

def draw_song_card(song, out_path):
    img = gradient(w, h)
    blobs(img)
    noise(img)

    card = (pad, pad, w - pad, h - pad)
    glass(img, card, radius=r, alpha=g_bg, blur=26, aa=4)

    d = ImageDraw.Draw(img)

    cover_size = 400
    cover_pad = 44
    cover = load_image(song.get("cover"), size=(500, 500))
    cover = crop_square(cover).resize((cover_size, cover_size), Image.LANCZOS)
    mask = Image.new("L", (cover_size, cover_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cover_size, cover_size), 28, fill=255)
    img.paste(cover, (pad + cover_pad, pad + cover_pad), mask)

    tx = pad + cover_pad + cover_size + 52
    ty = pad + 70
    right_pad = 44
    max_text_w = (w - pad) - tx - right_pad

    title_font = font(64, bold=True)
    artist_font = font(36)
    time_font = font(28)

    title = fit_text(d, song.get("title"), title_font, max_text_w)
    artist = fit_text(d, song.get("artist"), artist_font, max_text_w)

    d.text((tx, ty), title, font=title_font, fill=c_title)
    d.text((tx, ty + 92), artist, font=artist_font, fill=c_artist)
    d.text((tx, ty + 146), str(song.get("duration") or ""), font=time_font, fill=c_time)

    source = str(song.get("source") or "SoundCloud")
    badge_font = font(28, milker=True)

    icon_size = 34
    icon = load_icon(song.get("sourceIcon"), icon_size)
    icon_gap = 12
    left_pad = 22
    right_pad2 = 22

    text_w = d.textlength(source, font=badge_font)
    content_w = text_w + (icon_size + icon_gap if icon is not None else 0)

    badge_h = 52
    badge_w = int(left_pad + content_w + right_pad2)

    card_x1, card_y1, card_x2, card_y2 = pad, pad, w - pad, h - pad
    inset = 10

    badge_x = card_x2 - inset - badge_w
    badge_y = card_y2 - inset - badge_h

    if badge_x < card_x1 + inset:
        badge_x = card_x1 + inset
    if badge_y < card_y1 + inset:
        badge_y = card_y1 + inset


    badge_box = (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h)
    glass(img, badge_box, alpha=(255, 255, 255, 22), blur=18, pill=True)

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

song = {
    "cover": "https://avatars.githubusercontent.com/u/201022131?v=4",
    "title": "Anh yeu em",
    "artist": "Hạo Trann.",
    "duration": "12:12:11",
    "source": "soundcloud",
    "sourceIcon": "soundcloudIcon.png",
}

out_path = os.path.join(os.getcwd(), "eventCard.png")
draw_song_card(song, out_path)
print(out_path)