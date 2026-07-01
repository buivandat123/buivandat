import os
import json
import requests
import re
import math
import time
import random
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.5',
    'credits': 'kryzis X TXA',
    'description': 'Xem bản đồ vệ tinh, đường phố, địa hình với màu sắc đặc biệt',
    'power': 'Thành viên'
}

FONT_SIZE = "10"
CACHE_DIR = "modules/cache/checkmap"
os.makedirs(CACHE_DIR, exist_ok=True)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def _get_headers():
    return {'User-Agent': random.choice(USER_AGENTS)}

def _sty(text, color="#e8eaf6", bold=True):
    """Tạo style cho message với màu sắc"""
    lines = text.split("\n")
    h = len(lines[0]) + 1 if lines else 1
    styles = [
        MessageStyle(offset=0, length=len(text), style="font", size=FONT_SIZE, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
    ]
    if bold:
        styles.append(MessageStyle(offset=0, length=h, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def geocode_location_vietnamese(location):
    """Lấy tọa độ - ưu tiên Việt Nam"""
    cache_file = os.path.join(CACHE_DIR, f"geocode_{location.replace(' ', '_').replace('?', '')}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if time.time() - cached['time'] < 604800:
                    return cached['lat'], cached['lon'], cached['name']
        except:
            pass
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        search_query = f"{location}, Vietnam"
        
        params = {
            'q': search_query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'vn'
        }
        
        time.sleep(0.5)
        response = requests.get(url, params=params, headers=_get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                name = data[0].get('display_name', location)
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({'lat': lat, 'lon': lon, 'name': name, 'time': time.time()}, f)
                
                return lat, lon, name
        
        return None, None, None
    except Exception as e:
        print(f"[CHECKMAP] Lỗi geocode: {e}")
        return None, None, None

def get_map_from_cartodb(lat, lon, zoom, width=600, height=400):
    """Lấy bản đồ từ CartoDB (màu đẹp, ổn định)"""
    try:
        def deg2num(lat_deg, lon_deg, zoom):
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            xtile = int((lon_deg + 180.0) / 360.0 * n)
            ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return xtile, ytile
        
        xtile, ytile = deg2num(lat, lon, zoom)
        tile_url = f"https://a.basemaps.cartocdn.com/light_all/{zoom}/{xtile}/{ytile}.png"
        
        time.sleep(0.3)
        response = requests.get(tile_url, headers=_get_headers(), timeout=15)
        
        if response.status_code == 200:
            img_path = os.path.join(CACHE_DIR, f"map_{int(datetime.now().timestamp())}.png")
            with open(img_path, 'wb') as f:
                f.write(response.content)
            return img_path
        return None
    except Exception as e:
        print(f"[CHECKMAP] Lỗi CartoDB: {e}")
        return None

def get_satellite_esri(lat, lon, zoom, width=600, height=400):
    """Lấy ảnh vệ tinh từ ESRI"""
    try:
        lon_delta = 360 / (2 ** zoom) * (width / 256)
        lat_delta = lon_delta * (height / width)
        bbox = f"{lon - lon_delta},{lat - lat_delta},{lon + lon_delta},{lat + lat_delta}"
        
        url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        params = {
            'bbox': bbox,
            'bboxSR': 4326,
            'size': f"{width},{height}",
            'imageSR': 4326,
            'format': 'png',
            'f': 'image'
        }
        
        time.sleep(0.3)
        response = requests.get(url, params=params, headers=_get_headers(), timeout=15)
        
        if response.status_code == 200:
            img_path = os.path.join(CACHE_DIR, f"sat_{int(datetime.now().timestamp())}.png")
            with open(img_path, 'wb') as f:
                f.write(response.content)
            return img_path
        return None
    except Exception as e:
        print(f"[CHECKMAP] Lỗi ESRI: {e}")
        return None

def get_static_map(lat, lon, zoom, map_type, width=600, height=400):
    """Lấy bản đồ theo loại"""
    if map_type == "ve tinh":
        return get_satellite_esri(lat, lon, zoom, width, height)
    return get_map_from_cartodb(lat, lon, zoom, width, height)

def upload_to_catbox(file_path):
    """Upload ảnh lên catbox.moe"""
    try:
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': ('map.png', f, 'image/png')}
            data = {'reqtype': 'fileupload'}
            resp = requests.post('https://catbox.moe/user/api.php', files=files, data=data, timeout=30)
            if resp.status_code == 200:
                url = resp.text.strip()
                if url.startswith('http'):
                    return url
    except:
        pass
    return None

def handle_checkmap_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh checkmap"""
    prefix = client.settings.get("prefix", ".")
    
    raw_cmd = message.strip()
    if raw_cmd.startswith(prefix):
        raw_cmd = raw_cmd[len(prefix):].strip()
    
    if not raw_cmd.startswith("checkmap"):
        return
    
    content = raw_cmd[7:].strip()
    
    # ===== HIỂN THỊ HƯỚNG DẪN MÀU SẮC =====
    if not content or len(content) < 2:
        help_text = f"""
╔══════════════════════════════════════╗
║     🗺️  BẢN ĐỒ THẾ GIỚI  🗺️        ║
╠══════════════════════════════════════╣
║  📌 CÚ PHÁP:                         ║
║  {prefix}checkmap <địa điểm> [loại] [zoom]  ║
╠══════════════════════════════════════╣
║  📍 VÍ DỤ:                           ║
║  • {prefix}checkmap Hồ Chí Minh           ║
║  • {prefix}checkmap Hà Nội ve tinh       ║
║  • {prefix}checkmap Đà Nẵng 16           ║
╠══════════════════════════════════════╣
║  🗺️ LOẠI BẢN ĐỒ:                     ║
║  • duongpho → Đường phố (mặc định)   ║
║  • ve tinh  → Ảnh vệ tinh            ║
║  • diahinh  → Địa hình               ║
╠══════════════════════════════════════╣
║  🔍 ZOOM: 10-18 (15 là mặc định)     ║
╚══════════════════════════════════════╝
        """
        client.replyMessage(
            Message(text=help_text.strip(), style=_sty(help_text, "#00CED1", True)),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # ===== PARSE LỆNH =====
    parts = content.split()
    location_parts = []
    map_type = "duongpho"
    zoom = 15
    
    i = 0
    while i < len(parts):
        part = parts[i].lower()
        
        # Bỏ qua ký tự 'p' lỗi
        if part == "p" or part == "p." or part == "p," or part == "p?":
            i += 1
            continue
        
        if part in ["duongpho", "ve tinh", "diahinh", "duong", "thuong"]:
            map_type = part
            i += 1
            if i < len(parts) and parts[i].isdigit():
                zoom = min(18, max(10, int(parts[i])))
                i += 1
            break
        elif part.isdigit() and 10 <= int(part) <= 18:
            zoom = min(18, max(10, int(part)))
            i += 1
        else:
            location_parts.append(parts[i])
            i += 1
    
    location = " ".join(location_parts) if location_parts else content
    
    # ===== THÔNG BÁO ĐANG TÌM (màu cam) =====
    client.replyMessage(
        Message(text=f"🔍 Đang tìm bản đồ cho: {location}", style=_sty(f"🔍 Đang tìm bản đồ cho: {location}", "#FFA500", True)),
        message_object, thread_id, thread_type, ttl=8000
    )
    
    try:
        # Lấy tọa độ
        lat, lon, full_name = geocode_location_vietnamese(location)
        
        if lat is None:
            client.replyMessage(
                Message(text=f"❌ Không tìm thấy địa điểm: {location}\n\n💡 Hãy thử gõ tiếng Việt có dấu", style=_sty(f"❌ Không tìm thấy: {location}", "#FF4444", True)),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        # Tạo bản đồ
        img_path = get_static_map(lat, lon, zoom, map_type)
        
        if not img_path:
            raise Exception("Không thể tạo bản đồ, vui lòng thử lại")
        
        # Upload
        img_url = upload_to_catbox(img_path)
        
        # Tên hiển thị loại bản đồ
        type_names = {"duongpho": "ĐƯỜNG PHỐ", "ve tinh": "VỆ TINH", "diahinh": "ĐỊA HÌNH"}
        type_name = type_names.get(map_type, "ĐƯỜNG PHỐ")
        
        # Màu sắc theo loại bản đồ
        color_map = {
            "duongpho": "#00BFFF",  # Xanh dương
            "ve tinh": "#32CD32",   # Xanh lá
            "diahinh": "#FF8C00"    # Cam
        }
        text_color = color_map.get(map_type, "#00BFFF")
        
        # Rút gọn tên
        short_name = full_name[:50] + "..." if len(full_name) > 50 else full_name
        
        # Format kết quả đẹp
        result_text = f"""
╔════════════════════════════╗
║   🗺️  BẢN ĐỒ {type_name}  🗺️   ║
╠════════════════════════════╣
║ 📍 {short_name}
╠════════════════════════════╣
║ 📌 Tọa độ: {lat:.5f}, {lon:.5f}
║ 🔍 Zoom: {zoom}
╠════════════════════════════╣
║ 🟢 @{author_id.split(':')[-1][:10] if ':' in author_id else author_id[:10]}
╚════════════════════════════╝
        """
        
        if img_url:
            client.sendRemoteImage(
                imageurl=img_url,
                message=Message(text=result_text.strip(), style=_sty(result_text.strip(), text_color, True)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=600,
                height=400,
                ttl=120000
            )
        else:
            client.sendLocalImage(
                img_path,
                thread_id=thread_id,
                thread_type=thread_type,
                message=Message(text=result_text.strip(), style=_sty(result_text.strip(), text_color, True)),
                ttl=120000
            )
        
        # Xóa file tạm
        try:
            os.remove(img_path)
        except:
            pass
            
    except Exception as e:
        error_msg = str(e)[:100]
        client.replyMessage(
            Message(text=f"❌ LỖI: {error_msg}\n\nVui lòng thử lại sau", style=_sty(f"❌ LỖI: {error_msg}", "#FF4444", True)),
            message_object, thread_id, thread_type, ttl=30000
        )

def Kryzis():
    """Khởi tạo modeule"""
    return {"checkmap": handle_checkmap_command}