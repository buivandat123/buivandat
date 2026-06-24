import os
import json
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import random
import time
import concurrent.futures
from datetime import datetime

from zlapi.models import Message

des = {
    'version': "1.5.6",
    'credits': "kryzis X TXA",
    'description': "Check độ ngu",
    'power': "Thành viên"
}

CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
EMOJI_FONT_PATH = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")

if not os.path.exists(FONT_DIR):
    os.makedirs(FONT_DIR)

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
    except:
        try: 
            return ImageFont.truetype("arial.ttf", size)
        except: 
            return ImageFont.load_default()

def get_emoji_font(size):
    try: 
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: 
        return ImageFont.load_default()

def fetch_image(url):
    if not url: 
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: 
        return None

def fit_text_font(text, max_width, initial_size, min_size=15):
    current_size = initial_size
    font = get_font(current_size)
    text_str = str(text)
    
    while font.getlength(text_str) > max_width and current_size > min_size:
        current_size -= 2
        font = get_font(current_size)
    
    if font.getlength(text_str) > max_width:
        while font.getlength(text_str + "...") > max_width and len(text_str) > 3:
            text_str = text_str[:-1]
        text_str += "..."
    
    return font, text_str

def wrap_text(text, font, max_width, max_lines=None):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        
        if font.getlength(test_line) <= max_width:
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

def create_progress_bar_single(draw, x, y, width, height, value, color_theme="ngu"):
    radius = height // 2
    
    if color_theme == "ngu":
        bar_colors = [(255, 200, 50), (220, 160, 30)]
        bg_color = (70, 60, 40, 200)
    else:
        bar_colors = [(100, 220, 100), (60, 180, 60)]
        bg_color = (40, 60, 40, 200)
    
    draw.rounded_rectangle((x, y, x+width, y+height), 
                          radius=radius, fill=bg_color)
    
    bar_width = max(radius * 2, int((value / 100) * (width - radius * 2)))
    
    if bar_width > 0:
        draw.rounded_rectangle((x, y, x + bar_width, y+height), 
                              radius=radius, fill=bar_colors[0])
        
        if bar_width > radius * 2:
            for i in range(0, bar_width - radius * 2, 3):
                ratio = i / (bar_width - radius * 2)
                r = int(bar_colors[0][0] * (1 - ratio) + bar_colors[1][0] * ratio)
                g = int(bar_colors[0][1] * (1 - ratio) + bar_colors[1][1] * ratio)
                b = int(bar_colors[0][2] * (1 - ratio) + bar_colors[1][2] * ratio)
                draw.rectangle([x + radius + i, y, x + radius + i + 3, y + height], 
                              fill=(r, g, b))
    
    return bar_width

def create_glass_box(draw, x, y, w, h, radius=20, alpha=200):
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          fill=(50, 45, 35, alpha))
    
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          outline=(255, 255, 255, 40), width=2)

def detect_gender_simple(profile_data):
    gender_value = profile_data.get('gender', -1)
    gender_map = {0: "NAM", 1: "NỮ"}
    return gender_map.get(gender_value, "KHÔNG RÕ")

def analyze_ngu_only(profile_data, gender, is_admin_target=False):
    name = profile_data.get('name', 'Người dùng')
    avatar_url = profile_data.get('avatar', '')
    
    # Nếu là admin, kết quả luôn ở mức đặc biệt (thông minh nhất)
    if is_admin_target:
        return {
            'gender': gender,
            'ngu_score': 0,
            'orientation': "ADMIN SIÊU TRÍ TUỆ 🧠👑",
            'confidence': "100%",
            'description': "Admin là người lãnh đạo, trí tuệ siêu phàm! Không thể xác định độ ngu.",
            'emoji': "👑",
            'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'protected': True
        }
    
    seed_str = f"{name}{avatar_url}{gender}"
    seed = sum(ord(c) for c in seed_str) + int(time.time()) % 1000
    random.seed(seed)
    
    ngu_score = 50
    
    if avatar_url:
        if any(keyword in avatar_url.lower() for keyword in ['funny', 'meme', 'joke', 'stupid']):
            ngu_score += random.randint(10, 30)
        else:
            ngu_score += random.randint(-15, 15)
    else:
        ngu_score += random.randint(-10, 10)
    
    name_lower = name.lower()
    ngu_names = ['đần', 'ngu', 'ngốc', 'khờ', 'đồ', 'óc', 'trẻ', 'em', 'baby', 'kid']
    for ngu_name in ngu_names:
        if ngu_name in name_lower:
            ngu_score += random.randint(5, 20)
    
    ngu_score += random.randint(-20, 20)
    ngu_score = max(0, min(100, ngu_score))
    
    if ngu_score >= 90:
        orientation = "SIÊU NGU SIÊU CẤP 🤪"
        confidence = "99%"
        description = "Độ ngu đạt đến mức thần thánh! Có thể cần sự trợ giúp của chuyên gia."
    elif ngu_score >= 75:
        orientation = "NGU CHÍNH HIỆU 🤡"
        confidence = "88%"
        description = "Mức độ ngu rất cao, hành động thường xuyên không suy nghĩ."
    elif ngu_score >= 60:
        orientation = "NGU CÓ HẠNG 🐷"
        confidence = "75%"
        description = "Khá là ngu, đôi khi làm việc không cần não."
    elif ngu_score >= 45:
        orientation = "NGU VỪA VỪA 🙈"
        confidence = "65%"
        description = "Đôi lúc hơi ngu nhưng vẫn còn cứu được."
    elif ngu_score >= 30:
        orientation = "THÔNG MINH TÍNH 😎"
        confidence = "70%"
        description = "Khá thông minh, chỉ thi thoảng làm việc ngu ngốc."
    elif ngu_score >= 15:
        orientation = "THÔNG MINH RÕ RÀNG 🧠"
        confidence = "82%"
        description = "Khá thông minh, ít khi làm việc ngu ngốc."
    else:
        orientation = "THIÊN TÀI 🤓"
        confidence = "90%"
        description = "Cực kỳ thông minh, hầu như không bao giờ ngu."
    
    return {
        'gender': gender,
        'ngu_score': ngu_score,
        'orientation': orientation,
        'confidence': confidence,
        'description': description,
        'emoji': "🤪",
        'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'protected': False
    }

def create_ngu_banner_simple(profile_data, analysis_result, is_protected=False):
    width, height = 1000, 600
    bg = Image.new("RGBA", (width, height), (50, 45, 30))
    
    draw = ImageDraw.Draw(bg)
    
    for i in range(height):
        r = int(50 + i * 0.03)
        g = int(45 + i * 0.04)
        b = int(30 + i * 0.05)
        draw.line((0, i, width, i), fill=(r, g, b, 255))
    
    # Nếu là admin được bảo vệ, thêm watermark đặc biệt
    if is_protected:
        overlay = Image.new("RGBA", (width, height), (80, 70, 50, 150))
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)
    
    avatar_url = profile_data.get('avatar', '')
    avt_size = 150
    avt_x, avt_y = 50, 50
    
    avatar_img = fetch_image(avatar_url)
    if not avatar_img:
        avatar_img = Image.new("RGBA", (avt_size, avt_size), (255, 200, 50))
    
    mask = Image.new("L", (avt_size, avt_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avt_size, avt_size), fill=255)
    
    avatar_resized = avatar_img.resize((avt_size, avt_size), Image.Resampling.LANCZOS)
    avatar_circle = Image.new("RGBA", (avt_size, avt_size))
    avatar_circle.paste(avatar_resized, mask=mask)
    
    border_width = 5
    border_color = (100, 100, 100) if is_protected else (255, 180, 50)
    draw.ellipse((avt_x-border_width, avt_y-border_width, 
                  avt_x+avt_size+border_width, avt_y+avt_size+border_width), 
                outline=border_color, width=border_width)
    
    bg.paste(avatar_circle, (avt_x, avt_y), avatar_circle)
    
    text_x, text_y = 230, 60
    
    name = profile_data.get('name', 'Người dùng')
    if is_protected:
        name = f"[ADMIN] {name}"
    
    name_font, name_text = fit_text_font(name, 700, 48, min_size=30)
    draw.text((text_x, text_y), name_text, font=name_font, fill=(255, 255, 255))
    
    gender_text = f"Giới tính: {analysis_result['gender']}"
    draw.text((text_x, text_y + 60), gender_text, font=get_font(26), fill=(255, 240, 200))
    
    box_x, box_y = 50, 230
    box_width, box_height = 900, 320
    
    create_glass_box(draw, box_x, box_y, box_width, box_height, radius=20)
    
    draw.text((box_x + 30, box_y + 15), "🤪 PHÂN TÍCH ĐỘ NGU", font=get_font(28), fill=(255, 255, 255))
    
    bar_x, bar_y = box_x + 50, box_y + 75
    bar_width_total = 800
    bar_height = 50
    
    draw.text((bar_x, bar_y - 35), "MỨC ĐỘ NGU:", font=get_font(28), fill=(255, 240, 200))
    
    ngu_score = analysis_result['ngu_score']
    
    if is_protected:
        # Hiển thị thanh bar đặc biệt cho admin (độ ngu = 0)
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_width_total, bar_y + bar_height), 
                               radius=bar_height//2, fill=(60, 90, 60, 200))
        draw.text((bar_x + bar_width_total//2 - 50, bar_y + 10), "👑 ADMIN PROTECTED 👑", 
                  font=get_font(26), fill=(255, 215, 0))
    else:
        bar_width = create_progress_bar_single(draw, bar_x, bar_y, bar_width_total, bar_height, ngu_score, "ngu")
        
        value_text = f"{ngu_score}%"
        value_font = get_font(42)
        value_width = value_font.getlength(value_text)
        value_x = bar_x + bar_width_total + 20
        
        if value_x + value_width > box_x + box_width - 20:
            value_x = bar_x + bar_width_total - value_width - 10
        
        value_y = bar_y + (bar_height - value_font.size) // 2 + 2
        draw.text((value_x, value_y), value_text, font=value_font, fill=(255, 255, 200))
    
    info_y = bar_y + bar_height + 25
    
    orient_text = f"Phân loại: {analysis_result['orientation']}"
    draw.text((box_x + 50, info_y), orient_text, font=get_font(26), fill=(255, 220, 120))
    
    conf_y = info_y + 40
    conf_text = f"Độ tin cậy: {analysis_result['confidence']}"
    draw.text((box_x + 50, conf_y), conf_text, font=get_font(24), fill=(240, 200, 100))
    
    desc_start_y = conf_y + 45
    desc_font = get_font(22)
    max_desc_width = 800
    
    desc_lines = wrap_text(analysis_result['description'], desc_font, max_desc_width, 2)
    
    for i, line in enumerate(desc_lines):
        line_y = desc_start_y + i * 30
        draw.text((box_x + 50, line_y), line, font=desc_font, fill=(240, 240, 240))
    
    footer_y = box_y + box_height - 30
    
    watermark_text = "Ngu Analysis v1.5.6"
    if is_protected:
        watermark_text = "👑 ADMIN PROTECTED 👑"
    
    watermark_font = get_font(16)
    watermark_width = watermark_font.getlength(watermark_text)
    draw.text((width - watermark_width - 20, height - 25), watermark_text, font=watermark_font, fill=(180, 150, 100))
    
    draw.text((box_x + 20, box_y + box_height - 35), "🤡", font=get_emoji_font(24), fill=(255, 200, 50))
    draw.text((box_x + box_width - 50, box_y + box_height - 35), "🐷", font=get_emoji_font(24), fill=(255, 200, 50))
    
    return bg.convert("RGB")

def handle_ngu_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
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
        client.sendReaction(message_object, "🤡", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        if not user_info or not hasattr(user_info, 'changed_profiles'):
            client.replyMessage(Message(text="❌ Không thể lấy thông tin người dùng."), 
                              message_object, thread_id, thread_type)
            return

        profile = user_info.changed_profiles.get(str(target_id), {})
        
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
        analysis_result = analyze_ngu_only(profile_data, detected_gender, is_protected_target)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_ngu_banner_simple, profile_data, analysis_result, is_protected_target)
            image = future.result()

        timestamp = int(time.time())
        img_path = os.path.join(CACHE_PATH, f"ngu_{timestamp}.jpg")
        
        if not os.path.exists(CACHE_PATH):
            os.makedirs(CACHE_PATH)
            
        image.save(img_path, quality=95)
        
        if is_protected_target:
            result_text = (
                "👑 **ADMIN PROTECTED** 👑\n\n"
                f"👤 Tên: {profile_data['name']}\n"
                "⚠️ Tài khoản này được bảo vệ!\n"
                "Không thể thực hiện phân tích trên admin."
            )
        else:
            ngu_score = analysis_result['ngu_score']
            if ngu_score >= 70:
                prefix_text = "🤯 ÔI TRỜI ƠI!"
            elif ngu_score >= 50:
                prefix_text = "🤪 KẾT QUẢ ĐÂY!"
            elif ngu_score >= 30:
                prefix_text = "😅 CŨNG TẠM ĐƯỢC!"
            else:
                prefix_text = "🧠 KHÁ ĐẤY!"
            
            result_text = f"{prefix_text} KẾT QUẢ PHÂN TÍCH ĐỘ NGU:\n"
            result_text += f"👤 Tên: {profile_data['name']}\n"
            result_text += f"⚧️ Giới tính: {analysis_result['gender']}\n"
            result_text += f"🏷️ Phân loại: {analysis_result['orientation']}\n"
            result_text += f"📊 Mức độ Ngu: {ngu_score}%\n"
            result_text += f"📈 Độ tin cậy: {analysis_result['confidence']}\n"
            result_text += f"💬 {analysis_result['description']}"
        
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
            ngu_score = analysis_result['ngu_score']
            if ngu_score >= 70:
                client.sendReaction(message_object, "🤯", thread_id, thread_type)
            elif ngu_score >= 50:
                client.sendReaction(message_object, "🤪", thread_id, thread_type)
            elif ngu_score >= 30:
                client.sendReaction(message_object, "😅", thread_id, thread_type)
            else:
                client.sendReaction(message_object, "🧠", thread_id, thread_type)
            
        try: 
            os.remove(img_path)
        except: 
            pass

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi phân tích độ ngu: {str(e)}"), 
                          message_object, thread_id, thread_type)

def Kryzis():
    return {
        'ngu': handle_ngu_command,
        'nguu': handle_ngu_command,
        'checkngu': handle_ngu_command,
        'stupid': handle_ngu_command,
        'dốt': handle_ngu_command,
        'ngốc': handle_ngu_command
    }