# modules/mybot.py
# -*- coding: utf-8 -*-
import logging
import random
import re
import time
from typing import List, Tuple
from datetime import datetime, timedelta
import threading
import json
import os
import pytz
import signal
import subprocess
import io
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import *
import sys

# ============================================================
# CONFIG
# ============================================================

CONFIG_FILE = "config.json"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOT_PID_DIR = os.path.join(BASE_DIR, "data", "bot_pids")
BOT_SCRIPT_DIR = os.path.join(BASE_DIR, "data", "bot_scripts")

logging.basicConfig(level=logging.INFO, filename='bot_manager.log', encoding='utf-8')

des = {
    'version': "3.0.0",
    'credits': "Kryzis",
    'description': "Quản lý bot đa người dùng - Xịn Sò",
    'power': "Admin & User"
}

PREFIX = "."

try:
    from asset.config import API_KEY, SECRET_KEY
except:
    API_KEY = ""
    SECRET_KEY = ""

os.makedirs(BOT_PID_DIR, exist_ok=True)
os.makedirs(BOT_SCRIPT_DIR, exist_ok=True)

# ============================================================
# CANVAS
# ============================================================

def draw_bot_list(bots, author_name):
    W, H = 800, 400 + len(bots) * 60
    if H < 500:
        H = 500
    
    BG = (10, 14, 30)
    CARD = (20, 24, 50)
    BORDER = (60, 70, 120)
    TEXT = (230, 235, 250)
    SUB = (160, 170, 200)
    GREEN = (30, 200, 100)
    RED = (230, 60, 80)
    GOLD = (255, 200, 50)
    BLUE = (50, 150, 255)
    
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, W, 80], fill=CARD)
    draw.text((30, 20), f"📋 QUẢN LÝ BOT", font=Font(28, bold=True), fill=GOLD)
    draw.text((30, 55), f"👤 {author_name}  •  Tổng: {len(bots)} bot", font=Font(16), fill=SUB)
    draw.line([(0, 80), (W, 80)], fill=BORDER, width=2)
    
    if not bots:
        draw.text((W//2, H//2), "Chưa có bot nào!", font=Font(24), fill=SUB, anchor="mm")
    else:
        y = 100
        for i, bot in enumerate(bots, 1):
            x1, y1 = 20, y
            x2, y2 = W - 20, y + 55
            draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=CARD)
            draw.rounded_rectangle([x1, y1, x2, y2], radius=10, outline=BORDER, width=1)
            
            draw.text((40, y + 15), f"{i:02d}", font=Font(18, bold=True), fill=BLUE)
            status_icon = "🟢" if bot.get("status") else "🔴"
            running_icon = "✅" if bot.get("is_active") else "❌"
            draw.text((90, y + 15), f"{status_icon}{running_icon}", font=Font(16), fill=SUB)
            
            name = bot.get('username', 'Unknown')[:20]
            draw.text((140, y + 12), name, font=Font(20, bold=True), fill=TEXT)
            
            prefix = bot.get('prefix', '?')
            draw.text((140, y + 35), f"Prefix: {prefix}", font=Font(13), fill=SUB)
            
            het_han = bot.get('het_han', 'Vĩnh viễn')
            draw.text((W - 150, y + 12), f"📅 {het_han}", font=Font(13), fill=SUB)
            
            bot_id = str(bot.get('author_id', ''))[:8]
            draw.text((W - 150, y + 35), f"🆔 {bot_id}...", font=Font(12), fill=SUB)
            
            y += 60
    
    draw.line([(0, H - 30), (W, H - 30)], fill=BORDER, width=1)
    draw.text((30, H - 25), f"⚡ {len(bots)} bot", font=Font(12), fill=SUB)
    draw.text((W - 30, H - 25), "Kryzis Bot", font=Font(12), fill=SUB, anchor="ra")
    
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()

def Font(size, bold=False):
    try:
        paths = ["/system/fonts/Roboto-Regular.ttf", "/system/fonts/DroidSans.ttf"]
        if bold:
            paths = ["/system/fonts/Roboto-Bold.ttf", "/system/fonts/DroidSans-Bold.ttf"]
        for p in paths:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    except:
        pass
    return ImageFont.load_default()

def send_image(client, img_bytes, thread_id, thread_type, caption=""):
    try:
        tmp = f"/tmp/canvas_{int(time.time())}.png"
        with open(tmp, "wb") as f:
            f.write(img_bytes)
        result = client.sendLocalImage(tmp, thread_id=thread_id, thread_type=thread_type,
                              message=Message(text=caption) if caption else None,
                              ttl=60000)
        try:
            os.remove(tmp)
        except:
            pass
        return result
    except:
        return None

# ============================================================
# STYLE
# ============================================================

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

# ============================================================
# HÀM HỖ TRỢ
# ============================================================

def read_settings(user_id):
    try:
        settings_file = "asset/seting.json"
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def is_admin(author_id, client):
    try:
        settings = read_settings(author_id)
        admin_id = str(settings.get("admin", ""))
        adm_ids = [str(uid) for uid in settings.get("adm", [])]
        author_str = str(author_id)
        if author_str == admin_id or author_str in adm_ids:
            return True
        return False
    except:
        return False

def get_user_name_by_id(client, author_id):
    try:
        user_info = client.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except:
        return "Người dùng"

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"data": []}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_all_bots():
    config = load_config()
    bots = []
    for bot in config.get("data", []):
        if not bot.get("is_main_bot", False):
            bots.append(bot)
    return bots

def get_bot_by_index(index):
    bots = get_all_bots()
    if 1 <= index <= len(bots):
        return bots[index - 1]
    return None

def delete_bot_script(bot_id):
    script_path = os.path.join(BOT_SCRIPT_DIR, f"bot_{bot_id}.py")
    if os.path.exists(script_path):
        os.remove(script_path)
        return True
    return False

# ============================================================
# CHẠY BOT SONG SONG (THREAD)
# ============================================================

def start_bot_thread(target_bot, client, message_object, thread_id, thread_type):
    try:
        from main import MainBot
        
        imei = target_bot.get('imei')
        session_cookies = target_bot.get('session_cookies')
        bot_prefix = target_bot.get('prefix', '!')
        bot_id = target_bot.get('author_id')
        bot_name = target_bot.get('username', 'Unknown')
        
        if not API_KEY or not SECRET_KEY:
            _reply(client, message_object, thread_id, thread_type,
                   "❌ Thiếu API_KEY hoặc SECRET_KEY!", sty_err)
            return False
        
        if not imei or not session_cookies:
            _reply(client, message_object, thread_id, thread_type,
                   "❌ Bot thiếu IMEI hoặc Cookies!", sty_err)
            return False
        
        def run_bot():
            try:
                bot = MainBot(
                    api_key=API_KEY,
                    secret_key=SECRET_KEY,
                    imei=imei,
                    session_cookies=session_cookies
                )
                bot.settings = {"prefix": bot_prefix}
                bot._bot_enabled = True
                bot.listen()
            except Exception as e:
                print(f"[Bot] Lỗi: {e}")
        
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        
        _reply(client, message_object, thread_id, thread_type,
               f"✅ Bot {bot_name} đã chạy!", sty_ok)
        return True
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)
        return False

# ============================================================
# COMMAND HANDLERS
# ============================================================

def handle_mybot_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.split(maxsplit=2)
        if len(parts) < 2:
            _reply(client, message_object, thread_id, thread_type,
                   f"""📋 QUẢN LÝ BOT

.mybot help       - Trợ giúp
.mybot create     - Tạo bot mới
.mybot list       - Danh sách bot (ảnh)
.mybot info       - Thông tin bot
.mybot active     - Kích hoạt bot (admin)
.mybot shutdown   - Tắt bot (xóa local) (admin)
.mybot restart    - Khởi động lại bot (admin)
.mybot prefix     - Đổi prefix
.mybot rename     - Đổi tên bot
.mybot lock       - Khóa bot (admin)
.mybot unlock     - Mở khóa bot (admin)
.mybot del        - Xóa bot (admin)
.mybot manager    - Quản lý (admin)

💡 .mybot help [lệnh] - Xem chi tiết""", sty_info, ttl=60000)
            return

        subcommand = parts[1].lower()

        if subcommand == "help":
            handle_help_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "create":
            handle_create_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "list":
            handle_list_bots_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "info":
            handle_bot_info_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "active":
            handle_active_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "shutdown":
            handle_shutdown_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "restart":
            handle_restart_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "prefix":
            handle_change_prefix_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "rename":
            handle_rename_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "lock":
            handle_lock_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "unlock":
            handle_unlock_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "del":
            handle_del_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "manager":
            handle_manager_command(message, message_object, thread_id, thread_type, author_id, client)
        else:
            _reply(client, message_object, thread_id, thread_type,
                   f"❌ Lệnh {subcommand} không hỗ trợ!", sty_err)
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)

def handle_help_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split(maxsplit=2)
    if len(parts) >= 3:
        cmd = parts[2].lower()
        help_texts = {
            "create": """.mybot create [prefix] [imei] [cookies]""",
            "list": """.mybot list - Xem danh sách (ảnh)""",
            "active": """.mybot active [index] - Kích hoạt bot""",
            "shutdown": """.mybot shutdown [index] - Tắt bot (xóa local)""",
            "restart": """.mybot restart [index] - Khởi động lại""",
            "prefix": """.mybot prefix [new_prefix] - Đổi prefix""",
            "rename": """.mybot rename [index] [tên mới]""",
            "lock": """.mybot lock [index] - Khóa bot""",
            "unlock": """.mybot unlock [index] - Mở khóa bot""",
            "del": """.mybot del [index] - Xóa bot"""
        }
        text = help_texts.get(cmd, f"❌ Không có hướng dẫn cho lệnh {cmd}")
        _reply(client, message_object, thread_id, thread_type, text, sty_info, ttl=60000)
        return
    
    _reply(client, message_object, thread_id, thread_type,
           f"""📋 HƯỚNG DẪN MYBOT

⚡ LỆNH CƠ BẢN:
.mybot info       - Xem thông tin bot
.mybot prefix [p] - Đổi prefix
.mybot list       - Danh sách bot (ảnh)
.mybot rename [i] [tên] - Đổi tên bot

⚡ LỆNH ADMIN:
.mybot active [i] - Kích hoạt bot
.mybot shutdown [i] - Tắt bot (xóa local)
.mybot restart [i] - Khởi động lại
.mybot lock [i]   - Khóa bot
.mybot unlock [i] - Mở khóa bot
.mybot del [i]    - Xóa bot
.mybot manager    - Quản lý""", sty_info, ttl=60000)

def handle_create_command(message, message_object, thread_id, thread_type, author_id, client):
    source_name = get_user_name_by_id(client, author_id)
    
    if thread_type != ThreadType.USER:
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Lệnh này chỉ hoạt động trong inbox riêng!", sty_warn)
        return
    
    pattern = r"\[(.*?)\]\s*\[(.*?)\]\s*\[(.*?)\]"
    match = re.search(pattern, message)
    
    if not match:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot create [prefix] [imei] [cookies]\n💡 .mybot create [.] [857b9c28-...] [{{\"cookie\":\"value\"}}]", sty_info, ttl=60000)
        return
    
    bot_prefix, imei, raw_cookies = match.groups()
    bot_prefix = bot_prefix.strip()
    
    try:
        cookies = json.loads(raw_cookies)
    except:
        _reply(client, message_object, thread_id, thread_type,
               "❌ Cookies không hợp lệ!", sty_err)
        return
    
    config = load_config()
    
    for bot in config.get("data", []):
        if str(bot.get("author_id")) == str(author_id):
            _reply(client, message_object, thread_id, thread_type,
                   f"🚦 Bạn đã có bot!", sty_warn)
            return
    
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(vietnam_tz)
    
    config.setdefault("data", []).append({
        "prefix": bot_prefix,
        "api_key": API_KEY,
        "secret_key": SECRET_KEY,
        "imei": imei,
        "session_cookies": cookies,
        "is_main_bot": False,
        "username": source_name,
        "author_id": author_id,
        "status": False,
        "is_active": False,
        "kich_hoat": now.strftime("%d/%m/%Y"),
        "het_han": "Vĩnh viễn"
    })
    
    save_config(config)
    
    _reply(client, message_object, thread_id, thread_type,
           f"""✅ TẠO BOT THÀNH CÔNG

👤 {source_name} | 🆔 {author_id}
🚀 Prefix: {bot_prefix or 'không có'}
📅 {now.strftime('%d/%m/%Y')} | ⏰ Vĩnh viễn

💡 .mybot active {len(get_all_bots())} để chạy!""", sty_ok)

def handle_list_bots_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        bots = get_all_bots()
        author_name = get_user_name_by_id(client, author_id)
        
        img_bytes = draw_bot_list(bots, author_name)
        send_image(client, img_bytes, thread_id, thread_type)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)

def handle_bot_info_command(message, message_object, thread_id, thread_type, author_id, client):
    config = load_config()
    source_bot = None
    for bot in config.get("data", []):
        if str(bot.get("author_id")) == str(author_id):
            source_bot = bot
            break
    
    if not source_bot:
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn chưa có bot!", sty_warn)
        return
    
    _reply(client, message_object, thread_id, thread_type,
           f"""📋 THÔNG TIN BOT

👤 {source_bot.get('username', 'Unknown')}
🆔 {source_bot.get('author_id')}
📊 {'✅ Đang hoạt động' if source_bot.get('status') else '❌ Tạm dừng'}
📅 {source_bot.get('kich_hoat', 'N/A')}
⏰ {source_bot.get('het_han', 'Vĩnh viễn')}
🚀 {source_bot.get('prefix', 'Không có')}""", sty_info, ttl=60000)

def handle_active_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot active [index]\n💡 .mybot active 1", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        
        target_bot = get_bot_by_index(index)
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        target_name = target_bot["username"]
        target_bot["status"] = True
        target_bot["is_active"] = True
        save_config(load_config())
        
        _reply(client, message_object, thread_id, thread_type,
               f"✅ ACTIVE BOT THÀNH CÔNG\n👤 {target_name}\n⏰ {target_bot.get('het_han', 'Vĩnh viễn')}", sty_ok)
        
        start_bot_thread(target_bot, client, message_object, thread_id, thread_type)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)

def handle_shutdown_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot shutdown [index]", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        target_bot = get_bot_by_index(index)
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        bot_name = target_bot.get('username', 'Unknown')
        bot_id = target_bot.get('author_id')
        
        delete_bot_script(bot_id)
        remove_bot_pid(bot_id)
        
        target_bot["status"] = False
        target_bot["is_active"] = False
        save_config(load_config())
        
        _reply(client, message_object, thread_id, thread_type,
               f"""🛑 SHUTDOWN BOT THÀNH CÔNG

👤 Bot: {bot_name}
📊 Trạng thái: Đã tắt
🗑️ Đã xóa local bot!

💡 Dùng .mybot active {index+1} để bật lại""", sty_warn)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)

def handle_restart_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot restart [index]", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        target_bot = get_bot_by_index(index)
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        bot_name = target_bot.get('username', 'Unknown')
        bot_id = target_bot.get('author_id')
        
        delete_bot_script(bot_id)
        remove_bot_pid(bot_id)
        
        target_bot["status"] = True
        target_bot["is_active"] = True
        save_config(load_config())
        
        _reply(client, message_object, thread_id, thread_type,
               f"🔄 RESTART BOT THÀNH CÔNG\n👤 {bot_name}", sty_ok)
        
        start_bot_thread(target_bot, client, message_object, thread_id, thread_type)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)

def handle_change_prefix_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split(maxsplit=2)
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot prefix [new_prefix]", sty_info, ttl=60000)
        return
    
    new_prefix = parts[2].strip()
    if not new_prefix:
        _reply(client, message_object, thread_id, thread_type,
               "❌ Prefix không được để trống!", sty_err)
        return
    
    config = load_config()
    source_bot = None
    for bot in config.get("data", []):
        if str(bot.get("author_id")) == str(author_id):
            source_bot = bot
            break
    
    if not source_bot:
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn chưa có bot!", sty_warn)
        return
    
    old_prefix = source_bot.get('prefix', 'Không có')
    source_bot["prefix"] = new_prefix
    save_config(config)
    
    _reply(client, message_object, thread_id, thread_type,
           f"✅ ĐỔI PREFIX THÀNH CÔNG\n📌 Cũ: {old_prefix}\n📌 Mới: {new_prefix}", sty_ok)

def handle_rename_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split(maxsplit=3)
    if len(parts) < 4:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot rename [index] [tên mới]\n💡 .mybot rename 1 BotXịn", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        new_name = parts[3].strip()
        
        if not new_name:
            _reply(client, message_object, thread_id, thread_type,
                   "❌ Tên không được để trống!", sty_err)
            return
        
        config = load_config()
        target_bot = get_bot_by_index(index)
        
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        old_name = target_bot.get('username', 'Unknown')
        target_bot["username"] = new_name
        save_config(config)
        
        _reply(client, message_object, thread_id, thread_type,
               f"✅ ĐỔI TÊN BOT THÀNH CÔNG\n📌 Cũ: {old_name}\n📌 Mới: {new_name}", sty_ok)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)[:80]}", sty_err)

def handle_lock_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot lock [index]", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        target_bot = get_bot_by_index(index)
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        target_bot["status"] = False
        save_config(load_config())
        _reply(client, message_object, thread_id, thread_type,
               f"🔒 Đã khóa bot {target_bot.get('username', 'Unknown')}", sty_warn)
    except:
        _reply(client, message_object, thread_id, thread_type,
               "❌ Số thứ tự không hợp lệ!", sty_err)

def handle_unlock_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot unlock [index]", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        target_bot = get_bot_by_index(index)
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        target_bot["status"] = True
        save_config(load_config())
        _reply(client, message_object, thread_id, thread_type,
               f"🔓 Đã mở khóa bot {target_bot.get('username', 'Unknown')}", sty_ok)
    except:
        _reply(client, message_object, thread_id, thread_type,
               "❌ Số thứ tự không hợp lệ!", sty_err)

def handle_del_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot del [index]", sty_info, ttl=60000)
        return
    
    try:
        index = int(parts[2]) - 1
        target_bot = get_bot_by_index(index)
        if not target_bot:
            _reply(client, message_object, thread_id, thread_type,
                   "🚦 Không tìm thấy bot!", sty_warn)
            return
        
        delete_bot_script(target_bot.get('author_id'))
        remove_bot_pid(target_bot.get('author_id'))
        
        config = load_config()
        config["data"] = [bot for bot in config.get("data", []) if bot.get("author_id") != target_bot["author_id"]]
        save_config(config)
        _reply(client, message_object, thread_id, thread_type,
               f"🗑️ Đã xóa bot {target_bot.get('username', 'Unknown')}", sty_ok)
    except:
        _reply(client, message_object, thread_id, thread_type,
               "❌ Số thứ tự không hợp lệ!", sty_err)

def handle_manager_command(message, message_object, thread_id, thread_type, author_id, client):
    _reply(client, message_object, thread_id, thread_type,
           f"""👮 QUẢN TRỊ BOT

📋 .mybot list       - Danh sách bot (ảnh)
⚙️ .mybot active [i] - Kích hoạt bot
🛑 .mybot shutdown [i] - Tắt bot (xóa local)
🔄 .mybot restart [i] - Khởi động lại
🔒 .mybot lock [i]   - Khóa bot
🔓 .mybot unlock [i] - Mở khóa bot
🗑️ .mybot del [i]    - Xóa bot
📝 .mybot prefix [i] [new] - Đổi prefix (admin)
📝 .mybot rename [i] [tên] - Đổi tên bot

💡 .mybot active 1""", sty_info, ttl=60000)

# ============================================================
# LOAD
# ============================================================

def Kryzis():
    return {'mybot': handle_mybot_command}