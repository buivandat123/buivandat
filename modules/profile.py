# modules/profile.py
# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
from PIL import Image as PILImage
from zlapi.models import Message, ThreadType
from modules.canvas import *

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Xem hồ sơ người dùng",
    "power": "Thành viên"
}

CACHE_DIR = "/sdcard/download/kryzis/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache background theo theme
_bg_cache = {}
_avatar_cache = {}

def create_gradient(w, h, bg_top, bg_bot):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(
            int(bg_top[0] * (1 - t) + bg_bot[0] * t),
            int(bg_top[1] * (1 - t) + bg_bot[1] * t),
            int(bg_top[2] * (1 - t) + bg_bot[2] * t),
        ))
    return img.convert("RGBA")

def create_blobs(img, count=4):
    w, h = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(count):
        rr = random.randint(200, 350)
        x = random.randint(-150, w)
        y = random.randint(-150, h)
        d.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 40), (190, 120, 255, 35), (120, 255, 200, 30),
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(60)))

def create_noise(img):
    w, h = img.size
    n = Image.new("L", (w, h))
    px = n.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(125, 138)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 8))))

def get_background(w, h, is_dark=True):
    key = f"{w}_{h}_{is_dark}"
    if key in _bg_cache:
        return _bg_cache[key].copy()
    
    if is_dark:
        bg_top = (14, 18, 32)
        bg_bot = (6, 8, 16)
    else:
        bg_top = (245, 248, 255)
        bg_bot = (220, 225, 240)
    
    img = create_gradient(w, h, bg_top, bg_bot)
    create_blobs(img, count=4)
    create_noise(img)
    _bg_cache[key] = img
    return img.copy()

def get_user_info(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        profile = info.changed_profiles.get(str(uid), {})
        return {
            'name': profile.get('displayName', 'User'),
            'username': profile.get('username', ''),
            'avatar': profile.get('avatar', ''),
            'uid': uid,
            'gender': profile.get('gender'),
            'dob': profile.get('sdob', 'Chưa cập nhật'),
            'status': profile.get('status', ''),
            'isFriend': profile.get('isFr', 0),
            'isBlocked': profile.get('isBlocked', 0),
            'isActivePC': profile.get('isActivePC', 0),
            'isActiveWeb': profile.get('isActiveWeb', 0),
            'lastAction': profile.get('lastActionTime', 0),
            'created': profile.get('createdTs', 0),
            'biz': profile.get('bizPkg', {}),
        }
    except:
        return None

def format_gender(g):
    if g == 0:
        return "Nam"
    elif g == 1:
        return "Nữ"
    return "Ẩn"

def format_time(ts):
    if not ts:
        return "Không rõ"
    try:
        v = int(ts) / 1000 if int(ts) > 10_000_000_000 else int(ts)
        return datetime.fromtimestamp(v).strftime("%H:%M %d/%m/%Y")
    except:
        return str(ts)

def DrawProfileCard(user_data, out_path):
    # Kiểm tra trời sáng/tối (giờ địa phương)
    hour = datetime.now().hour
    is_dark = hour < 6 or hour >= 18
    
    w, h = 1200, 700
    pad = 40
    
    img = get_background(w, h, is_dark)
    
    # Color theme
    if is_dark:
        title_color = (246, 248, 255)
        text_color = (188, 196, 220)
        dim_color = (150, 158, 186)
        accent = (255, 200, 100)
        glass_alpha = (255, 255, 255, 28)
    else:
        title_color = (30, 35, 50)
        text_color = (80, 85, 110)
        dim_color = (150, 155, 175)
        accent = (255, 180, 50)
        glass_alpha = (255, 255, 255, 40)
    
    # Glass với alpha riêng
    def glass_custom(img, box, radius=35):
        x1, y1, x2, y2 = box
        bw, bh = x2 - x1, y2 - y1
        blur_img = img.crop(box).filter(ImageFilter.GaussianBlur(20))
        layer = Image.alpha_composite(blur_img, Image.new("RGBA", (bw, bh), glass_alpha))
        mask = RoundMask(bw, bh, radius)
        img.paste(layer, box, mask)
    
    card = (pad, pad, w - pad, h - pad)
    glass_custom(img, card, radius=35)
    
    d = ImageDraw.Draw(img)
    
    # Lấy dữ liệu
    name = user_data.get('name', 'Unknown')
    uid = user_data.get('uid', '')
    username = user_data.get('username', '')
    gender = format_gender(user_data.get('gender'))
    dob = user_data.get('dob', 'Chưa cập nhật')
    last = format_time(user_data.get('lastAction', 0))
    created = format_time(user_data.get('created', 0))
    
    biz = user_data.get('biz', {})
    if isinstance(biz, dict):
        label = biz.get('label', {})
        biz_name = label.get('VI', label.get('EN', 'Không')) if isinstance(label, dict) else 'Không'
    else:
        biz_name = 'Không'
    
    status = user_data.get('status', '')
    is_online = status == 'active'
    
    # === LAYOUT 2 CỘT ===
    LeftW = 320
    Gap = 25
    Inner = 22
    
    Lx1 = pad + Inner
    Ly1 = pad + Inner
    Lx2 = Lx1 + LeftW
    Ly2 = h - pad - Inner
    
    glass_custom(img, (Lx1, Ly1, Lx2, Ly2), radius=30)
    
    # Avatar
    avatar_size = 160
    avatar_url = user_data.get('avatar', '')
    avatar = LoadImage(avatar_url, (avatar_size, avatar_size))
    avatar = CircleCrop(avatar, avatar_size)
    
    avatar_x = Lx1 + (LeftW - avatar_size) // 2
    avatar_y = Ly1 + 30
    img.paste(avatar, (avatar_x, avatar_y), avatar)
    
    # Tên
    name_font = Font(28, bold=True)
    name_fit = FitText(d, name, name_font, LeftW - 40)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 18), name_fit, font=name_font, fill=title_color, anchor="mm")
    
    # Username
    if username:
        uname_font = Font(20)
        d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 52), f"@{username}", font=uname_font, fill=dim_color, anchor="mm")
    
    # Online status
    status_color = (0, 200, 0) if is_online else (255, 100, 100)
    status_text = "● Online" if is_online else "● Offline"
    status_font = Font(18, bold=is_online)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 82), status_text, font=status_font, fill=status_color, anchor="mm")
    
    # === BÊN PHẢI ===
    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = w - pad - Inner
    Ry2 = Ly2
    
    title_font = Font(32, bold=True)
    d.text(((Rx1 + Rx2) // 2, Ry1 + 25), "THÔNG TIN", font=title_font, fill=title_color, anchor="mm")
    
    # Danh sách thông tin
    info = [
        ("UID", uid),
        ("Giới tính", gender),
        ("Sinh nhật", dob),
        ("Hoạt động cuối", last),
        ("Ngày tham gia", created),
        ("Doanh nghiệp", biz_name),
    ]
    
    row_h = 42
    start_y = Ry1 + 80
    col1 = Rx1 + 25
    col2 = Rx1 + 170
    
    label_font = Font(22, bold=True)
    value_font = Font(22)
    
    for i, (label, value) in enumerate(info):
        y = start_y + i * row_h
        if y > Ry2 - 30:
            break
        d.text((col1, y), label + ":", font=label_font, fill=dim_color)
        d.text((col2, y), str(value)[:35], font=value_font, fill=text_color)
    
    # Footer
    footer_font = Font(16)
    d.text((w // 2, h - pad - 18), "Profile - Kryzis Bot", font=footer_font, fill=dim_color, anchor="mm")
    
    img.save(out_path, "PNG", optimize=True, compress_level=6)
    return out_path, w, h

def handle_profile(message, message_object, thread_id, thread_type, author_id, client):
    # Xác định user cần xem
    uid = author_id
    if message_object.mentions:
        uid = message_object.mentions[0]["uid"]
    elif len(message.strip().split()) > 1:
        parts = message.strip().split()
        if parts[1].isdigit():
            uid = parts[1]
    
    user_data = get_user_info(client, uid)
    if not user_data:
        client.replyMessage(Message(text="❌ Không tìm thấy user!"), message_object, thread_id, thread_type, ttl=60000)
        return
    
    out_path = os.path.join(CACHE_DIR, f"profile_{uid}_{int(time.time())}.png")
    DrawProfileCard(user_data, out_path)
    
    with PILImage.open(out_path) as im:
        w, h = im.size
    
    client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type,
                          message=Message(text=""), width=w, height=h)
    
    try:
        os.remove(out_path)
    except:
        pass

def LIGHT():
    return {"profile": handle_profile, "hs": handle_profile}
