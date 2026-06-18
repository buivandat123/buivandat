import os
import json
import requests
import urllib.parse
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.0',
    'credits': 'Yuta Bot',
    'description': 'Tìm kiếm địa điểm trên Google Map',
    'power': 'Thành viên'
}

FONT_SIZE = "9"

def _sty(text, color="#e8eaf6"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=FONT_SIZE, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def search_place(query):
    """Tìm kiếm địa điểm bằng Nominatim"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 5,
            'accept-language': 'vi'
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data:
                name = item.get('display_name', '').split(',')[0]
                results.append({
                    'name': name[:50],
                    'lat': item.get('lat', 0),
                    'lon': item.get('lon', 0),
                })
            return results
        return []
    except Exception as e:
        print(f"Lỗi: {e}")
        return []

def handle_map_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("map"):
        return
    
    keyword = cmd[3:].strip()
    
    if not keyword:
        help_text = f"""
🗺️ GOOGLE MAP

Cách dùng: {prefix}map <địa điểm>

Ví dụ:
{prefix}map Sài Gòn
{prefix}map Hà Nội
{prefix}map Đà Nẵng
        """
        client.replyMessage(
            Message(text=help_text.strip(), style=_sty(help_text, "#00BFFF")),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # Tìm kiếm
    results = search_place(keyword)
    
    if not results:
        client.replyMessage(
            Message(text=f"❌ Không tìm thấy '{keyword}'", style=_sty(f"❌ Không tìm thấy!", "#DB342E")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Gửi kết quả
    for i, place in enumerate(results[:3], 1):
        lat = place['lat']
        lon = place['lon']
        name = place['name']
        map_url = f"https://www.google.com/maps?q={lat},{lon}"
        
        msg = f"""
📍 KẾT QUẢ {i}: {name}
🗺️ {map_url}
📌 {lat}, {lon}
        """
        client.replyMessage(
            Message(text=msg.strip(), style=_sty(msg, "#e8eaf6")),
            message_object, thread_id, thread_type, ttl=60000
        )
        time.sleep(0.5)

def LIGHT():
    return {"map": handle_map_command}