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
import sys
from zlapi.models import *
import sys

# ============================================================
# CONFIG
# ============================================================

CONFIG_FILE = "config.json"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOT_PID_DIR = os.path.join(BASE_DIR, "data", "bot_pids")

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

# ============================================================
# CHẠY BOT TRONG THREAD + LƯU PID
# ============================================================

bot_threads = {}

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
        
        # Kill process cũ nếu có
        kill_bot_process(bot_id)
        time.sleep(0.5)
        
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
                
                # Lưu PID của thread
                import os
                save_bot_pid(bot_id, os.getpid())
                
                bot.listen()
            except Exception as e:
                print(f"[Bot] Lỗi: {e}")
            finally:
                if bot_id in bot_threads:
                    del bot_threads[bot_id]
                remove_bot_pid(bot_id)
        
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        bot_threads[bot_id] = thread
        
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
.mybot list       - Danh sách bot
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
            "create": """.mybot create [prefix] [imei] [cookies]
📌 Tạo bot mới
💡 Ví dụ: .mybot create [.] [857b9c28-...] [{"cookie":"value"}]""",
            "active": """.mybot active [index]
📌 Kích hoạt bot (cần admin)
💡 Ví dụ: .mybot active 1""",
            "shutdown": """.mybot shutdown [index]
📌 Tắt bot (cần admin)
💡 Ví dụ: .mybot shutdown 1""",
            "restart": """.mybot restart [index]
📌 Khởi động lại bot (cần admin)
💡 Ví dụ: .mybot restart 1""",
            "prefix": """.mybot prefix [new_prefix]
📌 Đổi prefix của bot
💡 Ví dụ: .mybot prefix !""",
            "rename": """.mybot rename [index] [tên mới]
📌 Đổi tên bot
💡 Ví dụ: .mybot rename 1 BotXịn""",
            "lock": """.mybot lock [index]
📌 Khóa bot (cần admin)
💡 Ví dụ: .mybot lock 1""",
            "unlock": """.mybot unlock [index]
📌 Mở khóa bot (cần admin)
💡 Ví dụ: .mybot unlock 1""",
            "del": """.mybot del [index]
📌 Xóa bot (cần admin)
💡 Ví dụ: .mybot del 1"""
        }
        text = help_texts.get(cmd, f"❌ Không có hướng dẫn cho lệnh {cmd}")
        _reply(client, message_object, thread_id, thread_type, text, sty_info, ttl=60000)
        return
    
    _reply(client, message_object, thread_id, thread_type,
           f"""📋 HƯỚNG DẪN MYBOT

⚡ LỆNH CƠ BẢN:
.mybot info       - Xem thông tin bot
.mybot prefix [p] - Đổi prefix
.mybot list       - Danh sách bot
.mybot rename [i] [tên] - Đổi tên bot

⚡ LỆNH ADMIN:
.mybot active [i] - Kích hoạt bot
.mybot shutdown [i] - Tắt bot
.mybot restart [i] - Khởi động lại
.mybot lock [i]   - Khóa bot
.mybot unlock [i] - Mở khóa bot
.mybot del [i]    - Xóa bot
.mybot manager    - Quản lý

💡 .mybot help [lệnh] - Xem chi tiết""", sty_info, ttl=60000)

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
               f"""📋 TẠO BOT

.mybot create [prefix] [imei] [cookies]

💡 Ví dụ:
.mybot create [.] [857b9c28-...] [{{"cookie":"value"}}]

📌 API_KEY và SECRET_KEY lấy từ asset/config.py""", sty_info, ttl=60000)
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

👤 Tên: {source_name}
🆔 ID: {author_id}
🚀 Prefix: {bot_prefix or 'không có'}
📅 Tạo: {now.strftime('%d/%m/%Y')}
⏰ Hết hạn: Vĩnh viễn

💡 Dùng .mybot active {len(get_all_bots())} để chạy bot!""", sty_ok)

def handle_list_bots_command(message, message_object, thread_id, thread_type, author_id, client):
    bots = get_all_bots()
    if not bots:
        _reply(client, message_object, thread_id, thread_type,
               "📋 Chưa có bot nào!", sty_info)
        return
    
    msg = "📋 DANH SÁCH BOT\n"
    for i, bot in enumerate(bots, 1):
        status = "✅" if bot.get("status") else "❌"
        running = "🟢" if bot.get("is_active") else "🔴"
        prefix = bot.get('prefix', '?')
        name = bot.get('username', 'Unknown')
        het_han = bot.get('het_han', 'N/A')
        msg += f"{i}. {status} {running} {name} | {prefix} | {het_han}\n"
    
    _reply(client, message_object, thread_id, thread_type, msg, sty_info, ttl=60000)

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

👤 Tên: {source_bot.get('username', 'Unknown')}
🆔 ID: {source_bot.get('author_id')}
📊 Trạng thái: {'✅ Đang hoạt động' if source_bot.get('status') else '❌ Tạm dừng'}
🟢 Đang chạy: {'✅' if source_bot.get('is_active') else '❌'}
📅 Kích hoạt: {source_bot.get('kich_hoat', 'N/A')}
⏰ Hết hạn: {source_bot.get('het_han', 'Vĩnh viễn')}
🚀 Prefix: {source_bot.get('prefix', 'Không có')}

💡 .mybot prefix [new] - Đổi prefix""", sty_info, ttl=60000)

def handle_active_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, message_object, thread_id, thread_type,
               "🚦 Bạn không có quyền!", sty_warn)
        return
    
    parts = message.split()
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"""📋 ACTIVE BOT

.mybot active [index]

💡 Ví dụ: .mybot active 1""", sty_info, ttl=60000)
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
               f"""✅ ACTIVE BOT THÀNH CÔNG

👤 Bot: {target_name}
⏰ Hết hạn: {target_bot.get('het_han', 'Vĩnh viễn')}

⏳ Đang khởi động bot...""", sty_ok)
        
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
        
        # Kill process (dùng PID của thread)
        if kill_bot_process(bot_id):
            target_bot["status"] = False
            target_bot["is_active"] = False
            save_config(load_config())
            
            _reply(client, message_object, thread_id, thread_type,
                   f"""🛑 SHUTDOWN BOT THÀNH CÔNG

👤 Bot: {bot_name}
📊 Trạng thái: Đã tắt

💡 Dùng .mybot active {index+1} để bật lại""", sty_warn)
        else:
            _reply(client, message_object, thread_id, thread_type,
                   f"⚠️ Bot {bot_name} không đang chạy!", sty_warn)
            target_bot["status"] = False
            target_bot["is_active"] = False
            save_config(load_config())
        
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
        
        # Kill process cũ
        kill_bot_process(bot_id)
        time.sleep(1)
        
        # Cập nhật trạng thái
        target_bot["status"] = True
        target_bot["is_active"] = True
        save_config(load_config())
        
        _reply(client, message_object, thread_id, thread_type,
               f"""🔄 RESTART BOT THÀNH CÔNG

👤 Bot: {bot_name}
📊 Trạng thái: Đang khởi động lại...""", sty_ok)
        
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
           f"""✅ ĐỔI PREFIX THÀNH CÔNG

📌 Cũ: {old_prefix}
📌 Mới: {new_prefix}

💡 Dùng: {new_prefix}help để xem lệnh""", sty_ok)

def handle_rename_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split(maxsplit=3)
    if len(parts) < 4:
        _reply(client, message_object, thread_id, thread_type,
               f"📋 .mybot rename [index] [tên mới]\n💡 Ví dụ: .mybot rename 1 BotXịn", sty_info, ttl=60000)
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
               f"""✅ ĐỔI TÊN BOT THÀNH CÔNG

📌 Cũ: {old_name}
📌 Mới: {new_name}""", sty_ok)
        
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
        
        # Kill process trước khi xóa
        kill_bot_process(target_bot.get('author_id'))
        
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

📋 DANH SÁCH:
.mybot list       - Xem danh sách bot

⚙️ QUẢN LÝ:
.mybot active [i] - Kích hoạt bot
.mybot shutdown [i] - Tắt bot
.mybot restart [i] - Khởi động lại
.mybot lock [i]   - Khóa bot
.mybot unlock [i] - Mở khóa bot
.mybot del [i]    - Xóa bot

📝 CÀI ĐẶT:
.mybot prefix [i] [new] - Đổi prefix (admin)
.mybot rename [i] [tên] - Đổi tên bot

💡 Ví dụ: .mybot active 1""", sty_info, ttl=60000)

# ============================================================
# LOAD
# ============================================================

def Kryzis():
    return {'mybot': handle_mybot_command}