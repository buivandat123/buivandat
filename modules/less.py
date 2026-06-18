import os
import json
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
import random
import time
import concurrent.futures
from datetime import datetime

from zlapi.models import Message

des = {
    'version': "1.5.7",
    'credits': "kryzis X TXA",
    'description': "Check độ les",
    'power': "Thành viên"
}

CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
EMOJI_FONT_PATH = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")

os.makedirs(CACHE_PATH, exist_ok=True)
os.makedirs(FONT_DIR, exist_ok=True)

# Danh sách admin UID (cần cập nhật theo admin thực tế)
ADMIN_UIDS = [
      "696983558841863982"
]

def is_admin(user_id):
    """Kiểm tra xem user có phải admin không"""
    return str(user_id) in ADMIN_UIDS

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

def get_emoji_font(size):
    try:
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def fetch_image(url):
    if not url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception:
        return None

def fit_text_font(text, max_width, initial_size, min_size=15):
    current_size = initial_size
    font = get_font(current_size)
    text_str = str(text)

    try:
        get_len = font.getlength
    except Exception:
        def get_len(s):
            return font.getsize(s)[0]

    while get_len(text_str) > max_width and current_size > min_size:
        current_size -= 2
        font = get_font(current_size)

    while get_len(text_str) > max_width and len(text_str) > 3:
        text_str = text_str[:-1]
    if get_len(text_str) > max_width:
        text_str = text_str[:-3] + "..."

    return font, text_str

def wrap_text(text, font, max_width, max_lines=None):
    words = text.split()
    lines = []
    current_line = ""

    try:
        get_len = font.getlength
    except Exception:
        def get_len(s):
            return font.getsize(s)[0]

    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        if get_len(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            if max_lines and len(lines) >= max_lines:
                if current_line:
                    lines.append(current_line + "...")
                break

    if current_line and (not max_lines or len(lines) < max_lines):
        lines.append(current_line)

    return lines

def create_progress_bar_single(draw, x, y, width, height, value, color_theme="les"):
    radius = height // 2

    if color_theme == "les":
        bar_colors = [(255, 105, 180), (220, 80, 160)]
        bg_color = (70, 40, 60, 200)
    else:
        bar_colors = [(100, 220, 100), (60, 180, 60)]
        bg_color = (40, 60, 40, 200)

    draw.rounded_rectangle((x, y, x + width, y + height), radius=radius, fill=bg_color)

    bar_width = max(radius * 2, int((value / 100) * (width - radius * 2)))
    bar_width = min(width, max(0, bar_width))

    if bar_width > 0:
        draw.rounded_rectangle((x, y, x + bar_width, y + height), radius=radius, fill=bar_colors[0])

        if bar_width > radius * 2:
            inner = bar_width - radius * 2
            step = 3
            for i in range(0, inner, step):
                ratio = i / max(1, inner)
                r = int(bar_colors[0][0] * (1 - ratio) + bar_colors[1][0] * ratio)
                g = int(bar_colors[0][1] * (1 - ratio) + bar_colors[1][1] * ratio)
                b = int(bar_colors[0][2] * (1 - ratio) + bar_colors[1][2] * ratio)
                draw.rectangle([x + radius + i, y, x + radius + i + step, y + height], fill=(r, g, b))

    return bar_width

def create_glass_box(draw, x, y, w, h, radius=20, alpha=200):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=(50, 35, 45, alpha))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=(255, 255, 255, 40), width=2)

def detect_gender_simple(profile_data):
    gender_value = profile_data.get('gender', -1)
    gender_map = {0: "NAM", 1: "NỮ"}
    return gender_map.get(gender_value, "KHÔNG RÕ")

def analyze_les_only(profile_data, gender, is_admin_target=False):
    name = profile_data.get('name', 'Người dùng')
    avatar_url = profile_data.get('avatar', '')

    # Nếu là admin, kết quả luôn ở mức thấp nhất hoặc đặc biệt
    if is_admin_target:
        return {
            'gender': gender,
            'les_score': 5,
            'orientation': "ADMIN KHÔNG THỂ CHECK 🔒",
            'confidence': "100%",
            'description': "Admin là người bảo vệ server! Không thể xác định xu hướng đồng tính nữ.",
            'emoji': "🔒",
            'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'protected': True
        }

    seed_str = f"{name}{avatar_url}{gender}"
    seed = sum(ord(c) for c in seed_str) + int(time.time()) % 1000
    random.seed(seed)

    les_score = 50

    if avatar_url:
        les_score += random.randint(-15, 25)
    else:
        les_score += random.randint(-10, 10)

    if gender == "NỮ":
        les_score += random.randint(0, 30)
    elif gender == "NAM":
        les_score -= random.randint(25, 45)

    les_score = max(0, min(100, les_score))

    if les_score >= 80:
        orientation = "LESBIAN CHÍNH HIỆU 🏳️‍🌈"
        confidence = "95%"
        description = "Phân tích cho thấy xu hướng đồng tính nữ rất rõ ràng với độ tin cậy cao."
    elif les_score >= 65:
        orientation = "CÓ THIÊN HƯỚNG LES 🌸"
        confidence = "83%"
        description = "Xu hướng đồng tính nữ khá rõ rệt, thể hiện qua nhiều đặc điểm phân tích."
    elif les_score >= 50:
        orientation = "KHẢ NĂNG LES TRUNG BÌNH 💫"
        confidence = "68%"
        description = "Có dấu hiệu của xu hướng đồng tính nữ nhưng chưa thực sự rõ ràng."
    elif les_score >= 35:
        orientation = "STRAIGHT MỞ 🌟"
        confidence = "58%"
        description = "Chủ yếu là straight nhưng có sự cởi mở với trải nghiệm đồng giới."
    else:
        orientation = "STRAIGHT RÕ RÀNG 👩‍❤️‍👨"
        confidence = "82%"
        description = "Xu hướng dị tính nữ rõ ràng, ít biểu hiện đồng tính."

    return {
        'gender': gender,
        'les_score': les_score,
        'orientation': orientation,
        'confidence': confidence,
        'description': description,
        'emoji': "🏳️‍🌈",
        'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'protected': False
    }

def create_les_banner_simple(profile_data, analysis_result, is_protected=False):
    width, height = 1000, 600
    bg = Image.new("RGBA", (width, height), (35, 20, 35))
    draw = ImageDraw.Draw(bg)

    for i in range(height):
        r = int(35 + i * 0.04)
        g = int(20 + i * 0.03)
        b = int(35 + i * 0.05)
        draw.line((0, i, width, i), fill=(r, g, b, 255))

    # Nếu là admin được bảo vệ, thêm watermark đặc biệt
    if is_protected:
        # Vẽ lớp phủ bảo vệ
        overlay = Image.new("RGBA", (width, height), (50, 30, 50, 150))
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

    avatar_url = profile_data.get('avatar', '')
    avt_size = 150
    avt_x, avt_y = 50, 50

    avatar_img = fetch_image(avatar_url)
    if not avatar_img:
        avatar_img = Image.new("RGBA", (avt_size, avt_size), (255, 105, 180))

    mask = Image.new("L", (avt_size, avt_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avt_size, avt_size), fill=255)

    avatar_resized = avatar_img.resize((avt_size, avt_size), Image.Resampling.LANCZOS)
    avatar_circle = Image.new("RGBA", (avt_size, avt_size))
    avatar_circle.paste(avatar_resized, mask=mask)

    border_width = 5
    border_color = (100, 100, 100) if is_protected else (255, 120, 200)
    draw.ellipse((avt_x - border_width, avt_y - border_width,
                  avt_x + avt_size + border_width, avt_y + avt_size + border_width),
                 outline=border_color, width=border_width)

    bg.paste(avatar_circle, (avt_x, avt_y), avatar_circle)

    text_x, text_y = 230, 60
    name = profile_data.get('name', 'Người dùng')
    
    if is_protected:
        name = f"[ADMIN] {name}"
    
    name_font, name_text = fit_text_font(name, 700, 48, min_size=30)
    draw.text((text_x, text_y), name_text, font=name_font, fill=(255, 255, 255))

    gender_text = f"Giới tính: {analysis_result['gender']}"
    draw.text((text_x, text_y + 60), gender_text, font=get_font(26), fill=(255, 200, 220))

    box_x, box_y = 50, 230
    box_width, box_height = 900, 320
    create_glass_box(draw, box_x, box_y, box_width, box_height, radius=20)

    draw.text((box_x + 30, box_y + 15), "🌸 PHÂN TÍCH XU HƯỚNG ĐỒNG TÍNH NỮ",
              font=get_font(28), fill=(255, 255, 255))

    bar_x, bar_y = box_x + 50, box_y + 75
    bar_width_total = 800
    bar_height = 50

    draw.text((bar_x, bar_y - 35), "MỨC ĐỘ LESBIAN:",
              font=get_font(28), fill=(255, 220, 240))

    les_score = analysis_result['les_score']
    
    if is_protected:
        # Hiển thị thanh bar đặc biệt cho admin
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_width_total, bar_y + bar_height), 
                               radius=bar_height//2, fill=(80, 80, 80, 200))
        draw.text((bar_x + bar_width_total//2 - 50, bar_y + 10), "🔒 PROTECTED 🔒", 
                  font=get_font(28), fill=(255, 200, 200))
    else:
        bar_width = create_progress_bar_single(draw, bar_x, bar_y, bar_width_total, bar_height, les_score, "les")
        
        value_text = f"{les_score}%"
        value_font = get_font(42)
        try:
            value_width = value_font.getlength(value_text)
        except Exception:
            value_width = value_font.getsize(value_text)[0]

        value_x = bar_x + bar_width_total + 20
        if value_x + value_width > box_x + box_width - 20:
            value_x = bar_x + bar_width_total - value_width - 10

        value_y = bar_y + (bar_height - value_font.size) // 2 + 2
        draw.text((value_x, value_y), value_text, font=value_font, fill=(255, 255, 200))

    info_y = bar_y + bar_height + 25
    orient_text = f"Xu hướng: {analysis_result['orientation']}"
    draw.text((box_x + 50, info_y), orient_text, font=get_font(26), fill=(255, 200, 220))

    conf_y = info_y + 40
    conf_text = f"Độ tin cậy: {analysis_result['confidence']}"
    draw.text((box_x + 50, conf_y), conf_text, font=get_font(24), fill=(240, 180, 220))

    desc_start_y = conf_y + 45
    desc_font = get_font(22)
    desc_lines = wrap_text(analysis_result['description'], desc_font, 800, 2)
    for i, line in enumerate(desc_lines):
        draw.text((box_x + 50, desc_start_y + i * 30), line, font=desc_font, fill=(240, 240, 240))

    watermark_text = "Lesbian Analysis v1.5.7"
    if is_protected:
        watermark_text = "🔒 ADMIN PROTECTED 🔒"
    
    watermark_font = get_font(16)
    try:
        w_w = watermark_font.getlength(watermark_text)
    except Exception:
        w_w = watermark_font.getsize(watermark_text)[0]

    draw.text((width - w_w - 20, height - 25), watermark_text, font=watermark_font, fill=(180, 100, 150))
    return bg.convert("RGB")

def handle_les_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    target_id = author_id
    if getattr(message_object, "mentions", None):
        target_id = message_object.mentions[0]['uid']
    elif getattr(message_object, "quote", None):
        target_id = message_object.quote.ownerId

    # Kiểm tra nếu target là admin
    if is_admin(target_id):
        # Người dùng thường không thể check admin
        if not is_admin(author_id):
            client.sendReaction(message_object, "🔒", thread_id, thread_type)
            client.replyMessage(Message(text="🔒 **BẢO VỆ ADMIN!**\n\nBạn không thể sử dụng lệnh này trên tài khoản admin."), 
                              message_object, thread_id, thread_type)
            return
        # Nếu chính admin check bản thân, vẫn cho phép nhưng hiển thị đặc biệt
        elif author_id == target_id:
            client.sendReaction(message_object, "👑", thread_id, thread_type)
    else:
        client.sendReaction(message_object, "🔍", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        profiles = getattr(user_info, "changed_profiles", {}) if user_info else {}
        profile = profiles.get(str(target_id), {})

        profile_data = {
            'name': profile.get('zaloName', 'Người dùng'),
            'avatar': profile.get('avatar', ''),
            'gender': profile.get('gender', -1),
            'dob': profile.get('dob', 0),
            'cover': profile.get('cover', ''),
            'globalId': profile.get('globalId', '')
        }

        detected_gender = detect_gender_simple(profile_data)
        is_protected_target = is_admin(target_id) and target_id != author_id
        analysis_result = analyze_les_only(profile_data, detected_gender, is_protected_target)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            image = executor.submit(create_les_banner_simple, profile_data, analysis_result, is_protected_target).result()

        ts = int(time.time())
        img_path = os.path.join(CACHE_PATH, f"les_{ts}.jpg")
        image.save(img_path, quality=95)

        if is_protected_target:
            result_text = (
                "🔒 **ADMIN PROTECTED** 🔒\n\n"
                f"👤 Tên: {profile_data['name']}\n"
                "⚠️ Tài khoản này được bảo vệ!\n"
                "Không thể thực hiện phân tích trên admin."
            )
        else:
            result_text = (
                "🌸 KẾT QUẢ PHÂN TÍCH ĐỒNG TÍNH NỮ:\n"
                f"👤 Tên: {profile_data['name']}\n"
                f"⚧️ Giới tính: {analysis_result['gender']}\n"
                f"🎯 Xu hướng: {analysis_result['orientation']}\n"
                f"📊 Mức độ Lesbian: {analysis_result['les_score']}%\n"
                f"💭 {analysis_result['description']}"
            )

        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=600,
            message=Message(text=result_text),
            ttl=120000
        )

        if not is_protected_target:
            client.sendReaction(message_object, "✅", thread_id, thread_type)
        
        try:
            os.remove(img_path)
        except Exception:
            pass

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi phân tích: {str(e)}"), message_object, thread_id, thread_type)

def LIGHT():
    return {
        'les': handle_les_command,
        'less': handle_les_command,
        'lescheck': handle_les_command,
        'kiemtrales': handle_les_command
    }