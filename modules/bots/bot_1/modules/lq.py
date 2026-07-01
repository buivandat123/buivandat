# modules/lq.py - DÙNG API LIÊN QUÂN
# -*- coding: utf-8 -*-
import os
import json
import re
import time
import requests
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': "1.0.0",
    'credits': "Kryzis",
    'description': "Lấy thông tin tướng và skin Liên Quân Mobile",
    'power': "User"
}

PREFIX = "."

# API Liên Quân (từ web garena)
API_URL = "https://api.lienquan.garena.vn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Dữ liệu tướng FULL (hardcode từ web, cập nhật khi có tướng mới)
ALL_HEROES = [
    "Sinestrea", "Thorne", "Allain", "Zata", "Yena", "Florentino", "Veres", 
    "Hayate", "Capheny", "Elsu", "D'Arcy", "Errol", "Enzo", "Zip", "Celica",
    "Volkath", "Krizzix", "Eland'orr", "Ishar", "Keera", "Ata", "Paine",
    "Laville", "Rouie", "Dextra", "Lorion", "Bijan", "Bonnie", "Teeri",
    "Yue", "Yan", "Aya", "Aoi", "Iggy", "Bright", "Qi", "Erin", "Ming",
    "Dirak", "Tachi", "Charlotte", "Dolia", "Biron", "Bolt Baron", "Billow",
    "Heino", "Goverra", "Edras", "Dyadia", "Flowborn", "Arum", "Wisp",
    "Max", "Liliana", "Tulen", "Omen", "Lindis", "TeeMee", "Moren",
    "Kil'Groth", "Xeniel", "Tel'Annas", "Astrid", "Ryoma", "Stuart",
    "Arduin", "Zill", "Murad", "Ignis", "Zuka", "Airi", "Kaine",
    "Lauriel", "Raz", "Skud", "Preyta", "Ilumia", "Slimz", "Arthur",
    "Kriknak", "Maloch", "Helen", "Jinna", "Cresht", "Natalya",
    "Lumburr", "Fennik", "Aleister", "Grakk", "Nakroth", "Taara",
    "Toro", "Yorn", "Gildur", "Alice", "Azzen'Ka", "Ormarr",
    "Butterfly", "Violet", "Chaugnar", "Zephys", "Kahlii",
    "Omega", "Mganga", "Krixi", "Mina", "Veera", "Thane", "Valhein",
    "The Flash", "Superman", "Wonder Woman"
]

# Cache dữ liệu skin/skill
_HERO_CACHE = {}

def _get_hero_data(hero_name):
    """Lấy dữ liệu tướng từ API hoặc cache"""
    hero_name = hero_name.lower()
    
    # Kiểm tra cache
    if hero_name in _HERO_CACHE:
        return _HERO_CACHE[hero_name]
    
    # Thử gọi API Garena
    try:
        # API lấy thông tin tướng
        resp = requests.get(
            f"{API_URL}/heroes/{hero_name}",
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                _HERO_CACHE[hero_name] = data["data"]
                return data["data"]
    except:
        pass
    
    # Fallback: tạo dữ liệu mẫu
    hero = {
        "name": hero_name.title(),
        "description": f"Thông tin về {hero_name.title()} đang được cập nhật.",
        "skills": [
            {"name": f"Skill 1", "description": "Mô tả skill 1"},
            {"name": f"Skill 2", "description": "Mô tả skill 2"},
            {"name": f"Skill 3", "description": "Mô tả skill 3"},
            {"name": f"Skill 4", "description": "Mô tả skill 4"}
        ],
        "skins": [
            {"name": f"{hero_name.title()} - Mặc định"},
            {"name": f"{hero_name.title()} - Skin 1"},
            {"name": f"{hero_name.title()} - Skin 2"}
        ]
    }
    _HERO_CACHE[hero_name] = hero
    return hero

def _sty(text, color="#e8eaf6", font_size="9"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=font_size, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def sty_ok(t):   return _sty(t, "#15A85F")
def sty_warn(t): return _sty(t, "#F7B503")
def sty_err(t):  return _sty(t, "#DB342E")
def sty_info(t): return _sty(t, "#00BFFF")

def _reply(client, obj, tid, ttype, text, sty=sty_info, ttl=60000):
    msg = Message(text=text, style=sty(text))
    return client.replyMessage(msg, obj, thread_id=tid, thread_type=ttype, ttl=ttl)

def handle_lq(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.strip().split()
        cmdb = f"{PREFIX}lq"
        
        if len(parts) < 2:
            menu = f"""📋 *LIÊN QUÂN MOBILE*

{cmdb} list          - Danh sách tướng (FULL)
{cmdb} info <tên>    - Thông tin tướng
{cmdb} skin <tên>    - Danh sách skin
{cmdb} skill <tên>   - Kỹ năng

💡 *Ví dụ:*
{cmdb} info sinestrea
{cmdb} skin sinestrea"""
            _reply(client, message_object, thread_id, thread_type, menu, sty_info)
            return

        cmd = parts[1].lower()

        if cmd == "list":
            msg = "📋 *DANH SÁCH TƯỚNG (FULL)*\n"
            # Hiển thị 20 tướng 1 lần
            for i, name in enumerate(ALL_HEROES, 1):
                msg += f"{i}. {name}\n"
                if i % 20 == 0 and i < len(ALL_HEROES):
                    _reply(client, message_object, thread_id, thread_type, msg, sty_info)
                    msg = ""
            if msg:
                _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        if len(parts) < 3:
            _reply(client, message_object, thread_id, thread_type, f"❌ Thiếu tên tướng!\n💡 {cmdb} {cmd} <tên>", sty_err)
            return

        hero_name = " ".join(parts[2:])
        
        # Tìm tướng trong danh sách
        found = None
        for name in ALL_HEROES:
            if hero_name.lower() in name.lower() or name.lower() in hero_name.lower():
                found = name
                break
        
        if not found:
            _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy tướng: {hero_name}", sty_err)
            return
        
        data = _get_hero_data(found)
        
        if cmd == "info":
            msg = f"""📋 *{data['name']}*

📝 {data['description'][:300]}...

⚔️ *Kỹ năng:*"""
            for skill in data["skills"][:4]:
                msg += f"\n  • {skill['name']}: {skill['description'][:100]}..."
            
            if data.get("skins"):
                msg += f"\n\n🎨 *Skin:* {', '.join([s['name'] for s in data['skins'][:5]])}"
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        if cmd == "skin":
            if not data.get("skins"):
                _reply(client, message_object, thread_id, thread_type, f"📋 *{data['name']}*\nKhông có skin nào", sty_info)
                return
            
            msg = f"🎨 *Skin của {data['name']}*\n"
            for i, skin in enumerate(data["skins"], 1):
                msg += f"{i}. {skin['name']}\n"
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        if cmd == "skill":
            if not data.get("skills"):
                _reply(client, message_object, thread_id, thread_type, f"📋 *{data['name']}*\nKhông có kỹ năng", sty_info)
                return
            
            msg = f"⚔️ *Kỹ năng của {data['name']}*\n"
            for skill in data["skills"]:
                msg += f"\n🔸 *{skill['name']}*\n{skill['description']}\n"
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        _reply(client, message_object, thread_id, thread_type, f"❌ Lệnh {cmd} không hỗ trợ!\n💡 {cmdb} để xem hướng dẫn", sty_err)

    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ Lỗi: {str(e)[:100]}", sty_err)

def Kryzis():
    return {'lq': handle_lq}
