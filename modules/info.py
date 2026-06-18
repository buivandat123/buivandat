from datetime import datetime
from io import BytesIO
import os
import random
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from zlapi.models import Message

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Xem thong tin nguoi dung",
    'power': "Member"
}

W = 1600
H = 950
PAD = 48

BgTop = (14, 18, 32)
BgBot = (6, 8, 16)

GlassFill = (255, 255, 255, 34)

TextTitle = (246, 248, 255, 255)
TextSub = (188, 196, 220, 255)
TextDim = (150, 158, 186, 255)

def Font(size, bold=False):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_fonts_dir = os.path.join(base_dir, "data", "fonts")
    
    paths = [
        os.path.join(local_fonts_dir, "Roboto-Regular.ttf"),
        os.path.join(local_fonts_dir, "DroidSans.ttf"),
        os.path.join(local_fonts_dir, "DejaVuSans.ttf"),
        os.path.join(local_fonts_dir, "NotoSans-Regular.ttf"),
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/DroidSans.ttf",
        "/system/fonts/NotoSans-Regular.ttf",
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
        "/system/fonts/NotoSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\tahomabd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in (bold_paths if bold else paths):
        try:
            return ImageFont.truetype(p, int(size))
        except:
            pass
    return ImageFont.load_default()

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

def WrapText(draw, text, font, max_width):
    """Tự động xuống dòng khi text quá dài"""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines if lines else [text]

def RoundMask(w, h, r, aa=4):
    mw, mh = w * aa, h * aa
    mr = int(min(r, w // 2, h // 2) * aa)
    m = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, mw, mh), mr, fill=255)
    return m.resize((w, h), Image.LANCZOS)

def Glass(canvas, box, radius=36, alpha=GlassFill, blur=24, aa=4):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    blur_img = canvas.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blur_img, Image.new("RGBA", (bw, bh), alpha))
    mask = RoundMask(bw, bh, radius, aa=aa)
    canvas.paste(layer, box, mask)

def SoftShadow(img, box, radius, blur=26, offset=(0, 10), alpha=90):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    dx, dy = offset
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    m = Image.new("L", (bw + blur * 4, bh + blur * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((blur * 2, blur * 2, blur * 2 + bw, blur * 2 + bh), radius, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    shadow = Image.new("RGBA", m.size, (0, 0, 0, alpha))
    layer.paste(shadow, (x1 + dx - blur * 2, y1 + dy - blur * 2), m)
    img.alpha_composite(layer)

def Gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(
            int(BgTop[0] * (1 - t) + BgBot[0] * t),
            int(BgTop[1] * (1 - t) + BgBot[1] * t),
            int(BgTop[2] * (1 - t) + BgBot[2] * t),
        ))
    return img.convert("RGBA")

def Blobs(img):
    w, h = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(8):
        rr = random.randint(300, 500)
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
            px[x, y] = random.randint(118, 140)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 14))))

def LoadImage(url, size):
    w, h = size
    def blank():
        return Image.new("RGBA", (w, h), (24, 26, 34, 255))
    if not url or not isinstance(url, str):
        return blank()
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return blank()
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
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

def ToDateTime(ts):
    if not ts:
        return "Khong ro"
    try:
        v = int(ts) / 1000 if int(ts) > 10000000000 else int(ts)
        return datetime.fromtimestamp(v).strftime("%d/%m/%Y %H:%M")
    except:
        return str(ts)

def CreateUserInfoCard(user_data, out_path):
    img = Gradient(W, H)
    Blobs(img)
    Noise(img)

    card = (PAD, PAD, W - PAD, H - PAD)
    SoftShadow(img, card, 40, blur=24, offset=(0, 8), alpha=85)
    Glass(img, card, radius=40)

    # Layout 2 cột
    LeftW = 380
    Gap = 30
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
    SoftShadow(img, LeftBox, 40, blur=24, offset=(0, 8), alpha=85)
    Glass(img, LeftBox, radius=40)

    d = ImageDraw.Draw(img)

    # ===== BEN TRAI: AVATAR =====
    avatar_size = 260
    avatar_url = user_data.get("avatar", "")
    avatar = LoadImage(avatar_url, (500, 500))
    avatar = CircleCrop(avatar, avatar_size)

    avatar_x = Lx1 + (LeftW - avatar_size) // 2
    avatar_y = Ly1 + 30
    img.paste(avatar, (avatar_x, avatar_y), avatar)

    name = user_data.get("displayName", "Unknown")
    uid = user_data.get("userId", "Unknown")
    status = user_data.get("status", "Khong ro")

    name_font = Font(34, bold=True)
    sub_font = Font(24)

    name_fit = FitText(d, name, name_font, LeftW - 50)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 20), name_fit, font=name_font, fill=TextTitle, anchor="mm")

    is_online = status == "active"
    status_color = "#27c93f" if is_online else "#ffbd2e"
    status_text = "Online" if is_online else "Offline"
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 60), status_text, font=sub_font, fill=status_color, anchor="mm")

    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 95), f"UID: {uid}", font=sub_font, fill=TextSub, anchor="mm")

    # ===== BEN PHAI: THONG TIN XUONG DONG =====
    gender = user_data.get("gender")
    gender_str = "Nam" if gender == 0 else "Nu" if gender == 1 else "An"
    
    biz = user_data.get("bizPkg", {})
    if isinstance(biz, dict):
        label = biz.get("label", {})
        biz_name = label.get("VI", label.get("EN", "Khong")) if isinstance(label, dict) else "Khong"
    else:
        biz_name = "Khong"

    is_friend = "Co" if user_data.get("isFr") == 1 else "Khong"
    is_blocked = "Co" if user_data.get("isBlocked") == 1 else "Khong"
    username = user_data.get("username", "Khong co")
    dob = user_data.get("sdob", "An")

    label_font = Font(28, bold=True)
    value_font = Font(26)

    x1 = Rx1 + 25
    y1 = Ry1 + 30
    col_w = 160
    max_value_w = Rx2 - x1 - col_w - 30
    row_h = 55

    # Dòng 1: Giới tính
    d.text((x1, y1), "Gioi tinh:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y1), gender_str, font=value_font, fill=TextSub)

    # Dòng 2: Sinh nhật
    y2 = y1 + row_h
    d.text((x1, y2), "Sinh nhat:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y2), dob, font=value_font, fill=TextSub)

    # Dòng 3: Username
    y3 = y2 + row_h
    d.text((x1, y3), "Username:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y3), FitText(d, username, value_font, max_value_w), font=value_font, fill=TextSub)

    # Dòng 4: Bạn bè
    y4 = y3 + row_h
    d.text((x1, y4), "Ban be:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y4), is_friend, font=value_font, fill=TextSub)

    # Dòng 5: Bị chặn
    y5 = y4 + row_h
    d.text((x1, y5), "Bi chan:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y5), is_blocked, font=value_font, fill=TextSub)

    # Dòng 6: Business
    y6 = y5 + row_h
    d.text((x1, y6), "Business:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y6), FitText(d, biz_name, value_font, max_value_w), font=value_font, fill=TextSub)

    # Dòng 7: Hoạt động lần cuối
    last_active = ToDateTime(user_data.get('lastActionTime', 0))
    y7 = y6 + row_h + 10
    d.text((x1, y7), "Hoat dong lan cuoi:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y7), FitText(d, last_active, value_font, max_value_w), font=value_font, fill=TextSub)

    # Dòng 8: Ngày tạo
    created = ToDateTime(user_data.get('createdTs', 0))
    y8 = y7 + row_h
    d.text((x1, y8), "Ngay tao:", font=label_font, fill=TextDim)
    d.text((x1 + col_w, y8), FitText(d, created, value_font, max_value_w), font=value_font, fill=TextSub)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path

def handle_info(message, message_object, thread_id, thread_type, author_id, client):
    uid = None
    if message_object.mentions:
        uid = message_object.mentions[0]["uid"]
    elif getattr(message_object, "quote", None):
        uid = str(message_object.quote.ownerId)
    else:
        parts = message.split()
        if len(parts) > 1 and parts[1].isdigit():
            uid = parts[1]
    if not uid:
        uid = author_id

    try:
        p = client.fetchUserInfo(uid).changed_profiles.get(str(uid), {})
        if not p:
            client.replyMessage(Message(text="Khong tim thay thong tin user!"),
                              message_object, thread_id, thread_type, ttl=60000)
            return

        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "info_cache")
        os.makedirs(cache_dir, exist_ok=True)
        out_path = f"{cache_dir}/user_info_{uid}.png"

        CreateUserInfoCard(p, out_path)

        client.sendLocalImage(
            out_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text="")
        )

        try:
            os.remove(out_path)
        except:
            pass

    except Exception as e:
        client.replyMessage(Message(text=f"Loi: {str(e)[:80]}"),
                          message_object, thread_id, thread_type, ttl=60000)

def LIGHT():
    return {"info": handle_info}