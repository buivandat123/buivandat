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
from modules.canvas import *

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

def save_bot_pid(bot_id, pid):
    pid_file = os.path.join(BOT_PID_DIR, f"{bot_id}.pid")
    with open(pid_file, 'w') as f:
        f.write(str(pid))

def get_bot_pid(bot_id):
    pid_file = os.path.join(BOT_PID_DIR, f"{bot_id}.pid")
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            return int(f.read())
    return None

def remove_bot_pid(bot_id):
    pid_file = os.path.join(BOT_PID_DIR, f"{bot_id}.pid")
    if os.path.exists(pid_file):
        os.remove(pid_file)
        return True
    return False

def kill_bot_process(bot_id):
    pid = get_bot_pid(bot_id)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
            remove_bot_pid(bot_id)
            return True
        except:
            pass
    return False

def delete_bot_script(bot_id):
    script_path = os.path.join(BOT_SCRIPT_DIR, f"bot_{bot_id}.py")
    if os.path.exists(script_path):
        os.remove(script_path)
        return True
    return False

def delete_bot_local(bot_id):
    """Xóa toàn bộ local của bot (script + pid)"""
    delete_bot_script(bot_id)
    remove_bot_pid(bot_id)

# ============================================================
# CHẠY BOT SONG SONG (THREAD)
# ============================================================

def start_bot_thread(target_bot, client, message_object, thread_id, thread_type):
    try:
        from main import MainBot
        
        imei = target_bot.get('imei')
        session_cookies = target_bot.get('session_cookies')
        bot_prefix = target_bot.get('prefix', '!')
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
.mybot shutdown   - Tắt bot (admin)
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
            "shutdown": """.mybot shutdown [index] - Tắt bot""",
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
.mybot shutdown [i] - Tắt bot
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
    """Hiển thị danh sách bot dạng ảnh canvas"""
    try:
        bots = get_all_bots()
        
        # Dùng canvas để vẽ
        W, H = 1600, 400 + len(bots) * 80
        if H < 500:
            H = 500
        
        img = CreateBackground(W, H)
        
        # Card chính
        card = (PAD, PAD, W - PAD, H - PAD)
        Glass(img, card, radius=40, alpha=(255, 255, 255, 15))
        
        d = ImageDraw.Draw(img)
        
        # Header
        d.text((W//2, PAD + 30), "📋 QUẢN LÝ BOT", font=Font(40, bold=True), fill=(255, 200, 100), anchor="mm")
        d.line((PAD + 100, PAD + 80, W - PAD - 100, PAD + 80), fill=(255, 255, 255, 30), width=2)
        
        d.text((PAD + 80, PAD + 115), f"👤 {get_user_name_by_id(client, author_id)}", font=Font(26), fill=(200, 200, 255))
        d.text((W - PAD - 80, PAD + 115), f"📦 Tổng: {len(bots)} bot", font=Font(26), fill=(200, 200, 255), anchor="ra")
        
        if not bots:
            d.text((W//2, H//2), "Chưa có bot nào!", font=Font(30), fill=(150, 150, 200), anchor="mm")
        else:
            y = PAD + 160
            for i, bot in enumerate(bots, 1):
                x1 = PAD + 40
                x2 = W - PAD - 40
                y1 = y
                y2 = y + 65
                
                # Card con
                Glass(img, (x1, y1, x2, y2), radius=18, alpha=(255, 255, 255, 10))
                
                # Số thứ tự
                d.text((x1 + 25, y + 22), f"{i:02d}", font=Font(24, bold=True), fill=(100, 200, 255))
                
                # Trạng thái
                status = "🟢" if bot.get("status") else "🔴"
                running = "✅" if bot.get("is_active") else "❌"
                d.text((x1 + 90, y + 22), f"{status} {running}", font=Font(20), fill=(200, 200, 200))
                
                # Tên
                name = bot.get('username', 'Unknown')[:25]
                d.text((x1 + 160, y + 15), name, font=Font(28, bold=True), fill=(255, 255, 255))
                
                # Prefix
                prefix = bot.get('prefix', '?')
                d.text((x1 + 160, y + 45), f"Prefix: {prefix}", font=Font(18), fill=(180, 180, 200))
                
                # Hết hạn
                het_han = bot.get('het_han', 'Vĩnh viễn')
                d.text((x2 - 180, y + 15), f"📅 {het_han}", font=Font(18), fill=(180, 180, 200), anchor="ra")
                
                # ID
                bot_id = str(bot.get('author_id', ''))[:8]
                d.text((x2 - 180, y + 45), f"🆔 {bot_id}...", font=Font(16), fill=(150, 150, 180), anchor="ra")
                
                y += 75
        
        # Footer
        footer_y = H - PAD - 30
        d.line((PAD + 80, footer_y, W - PAD - 80, footer_y), fill=(255, 255, 255, 15), width=1)
        
        d.text((PAD + 90, footer_y + 10), f"⚡ {len(bots)} bot", font=Font(20), fill=(150, 150, 200))
        d.text((W - PAD - 90, footer_y + 10), "Kryzis Bot", font=Font(20), fill=(150, 150, 200), anchor="ra")
        
        # Lưu ảnh
        out_path = os.path.join(BOT_PID_DIR, f"bot_list_{int(time.time())}.png")
        img.save(out_path, "PNG", optimize=True)
        
        with Image.open(out_path) as im:
            w, h = im.size
        
        client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type, 
                              message=Message(text=""), width=w, height=h)
        try:
            os.remove(out_path)
        except:
            pass
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi vẽ ảnh: {str(e)[:80]}", sty_err)

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
        
        # Xóa local
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
        
        # Xóa local
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
🛑 .mybot shutdown [i] - Tắt bot
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