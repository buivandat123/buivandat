import os
import json
from PIL import ImageFont
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': "3.0.0",
    'credits': "Yuta Bot",
    'description': "Quan ly font chung cho toan bo bot - Ap dung cho moi lenh",
    'power': "Admin"
}

FONT_DIR = "modules/cache/font"
FONT_CONFIG_FILE = "modules/cache/font_config.json"
os.makedirs(FONT_DIR, exist_ok=True)

DEFAULT_FONT = "LazerGameZone.ttf"

# Cache font hien tai
_current_font = None

def get_current_font():
    """Lay font dang duoc chon"""
    global _current_font
    if _current_font:
        return _current_font
    try:
        with open(FONT_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _current_font = data.get("current_font", DEFAULT_FONT)
            return _current_font
    except:
        return DEFAULT_FONT

def set_current_font(font_name):
    """Luu font dang duoc chon"""
    global _current_font
    try:
        with open(FONT_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"current_font": font_name}, f, ensure_ascii=False, indent=2)
        _current_font = font_name
        return True
    except:
        return False

def get_font_path(font_name=None):
    if font_name:
        font_path = os.path.join(FONT_DIR, font_name)
        if os.path.exists(font_path):
            return font_path
    
    current = get_current_font()
    font_path = os.path.join(FONT_DIR, current)
    if os.path.exists(font_path):
        return font_path
    
    if os.path.exists(FONT_DIR):
        for f in os.listdir(FONT_DIR):
            if f.endswith(('.ttf', '.otf')):
                return os.path.join(FONT_DIR, f)
    return None

def get_font(size):
    """Lay font - DUNG CHO MOI MODULE CAN HIEN THI ANH"""
    font_path = get_font_path()
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def get_available_fonts():
    fonts = []
    if os.path.exists(FONT_DIR):
        for f in os.listdir(FONT_DIR):
            if f.endswith(('.ttf', '.otf')):
                fonts.append(f)
    return fonts

def is_admin(author_id):
    try:
        with open("asset/seting.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            owner = str(data.get("admin", ""))
            admins = [str(x) for x in data.get("adm", [])]
            return str(author_id) == owner or str(author_id) in admins
    except:
        return False

def _reply(client, text, message_object, thread_id, thread_type):
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False)]
    client.replyMessage(Message(text=text, style=MultiMsgStyle(styles)), message_object, thread_id, thread_type, ttl=60000)

def handle_font_command(message, message_object, thread_id, thread_type, author_id, client):
    """Lenh quan ly font - ap dung cho toan bot"""
    if not is_admin(author_id):
        _reply(client, "🚫 Chi admin moi dung duoc lenh nay!", message_object, thread_id, thread_type)
        return

    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    if not cmd.startswith("font"):
        return
    
    content = cmd[4:].strip()
    parts = content.split()
    sub = parts[0].lower() if parts else ""
    
    if sub == "list":
        fonts = get_available_fonts()
        current = get_current_font()
        if fonts:
            text = "📁 DANH SACH FONT TRONG CACHE:\n━━━━━━━━━━━━━━━━━━\n"
            for f in fonts:
                mark = "🌟 " if f == current else "📄 "
                text += f"{mark}{f}\n"
            text += f"\n💡 Font dang dung: {current}"
            text += f"\n💡 Chuyen font: {prefix}font set <tenfont>"
            text += f"\n💡 Thu muc font: {FONT_DIR}"
        else:
            text = f"📭 Chua co font nao trong thu muc {FONT_DIR}\n💡 Hay bo font .ttf vao day de su dung"
        _reply(client, text, message_object, thread_id, thread_type)
    
    elif sub == "set":
        if len(parts) < 2:
            _reply(client, f"📋 Dung: {prefix}font set <tenfont>\nVD: {prefix}font set {DEFAULT_FONT}", 
                   message_object, thread_id, thread_type)
            return
        
        font_name = parts[1]
        font_path = os.path.join(FONT_DIR, font_name)
        
        if os.path.exists(font_path):
            set_current_font(font_name)
            _reply(client, f"✅ Da chuyen sang font: {font_name}\n💡 Font da duoc ap dung ngay cho tat ca lenh!", 
                   message_object, thread_id, thread_type)
        else:
            fonts = get_available_fonts()
            if fonts:
                text = f"❌ Khong tim thay font '{font_name}'\n\n📁 Cac font co san:\n"
                for f in fonts:
                    text += f"   • {f}\n"
                _reply(client, text, message_object, thread_id, thread_type)
            else:
                _reply(client, f"❌ Khong tim thay font '{font_name}'\n📁 Thu muc font: {FONT_DIR}", 
                       message_object, thread_id, thread_type)
    
    elif sub == "current":
        current = get_current_font()
        font_path = get_font_path()
        if font_path:
            size = os.path.getsize(font_path) / 1024
            text = f"🌟 FONT DANG DUNG:\n━━━━━━━━━━━━━━━━━━\n📄 Ten: {current}\n📦 Kich thuoc: {size:.1f} KB\n📁 Duong dan: {font_path}"
        else:
            text = f"❌ Khong tim thay font '{current}'!"
        _reply(client, text, message_object, thread_id, thread_type)
    
    elif sub == "path":
        text = f"📁 Duong dan thu muc font:\n{FONT_DIR}\n\n📄 Cac font hien co:"
        fonts = get_available_fonts()
        current = get_current_font()
        if fonts:
            for f in fonts:
                mark = " 🌟 (dang dung)" if f == current else ""
                text += f"\n   - {f}{mark}"
        else:
            text += "\n   (chua co font)"
        _reply(client, text, message_object, thread_id, thread_type)
    
    else:
        help_text = f"""
📝 QUAN LY FONT CHUNG CHO TOAN BOT

Cach dung:
{prefix}font list        — Xem danh sach font
{prefix}font set <ten>   — Chuyen font (ap dung ngay)
{prefix}font current     — Xem font dang dung
{prefix}font path        — Xem duong dan thu muc

Vi du:
{prefix}font list
{prefix}font set LazerGameZone.ttf

Sau khi doi font, tat ca lenh tao anh se dung font moi!
        """
        _reply(client, help_text.strip(), message_object, thread_id, thread_type)

def LIGHT():
    return {"font": handle_font_command}