# modules/mybot.py - THÊM ADMIN ID
# -*- coding: utf-8 -*-
import os
import json
import time
import random
import re
import threading
import shutil
import importlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle

des = {
    'version': "2.0.0",
    'credits': "Kryzis",
    'description': "Quản lý bot đa người dùng",
    'power': "Quản trị viên và thành viên"
}

PREFIX = ">"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIN_FILE = os.path.join(BASE_DIR, "asset", "config", "login.json")
MULTIBOT_DIR = os.path.join(BASE_DIR, "asset", "config", "multibot")
BOT_MODULES_DIR = os.path.join(BASE_DIR, "modules", "bots")
MODULES_DIR = os.path.join(BASE_DIR, "modules")

# ============================================================
# GMAIL CONFIG
# ============================================================

GMAIL = {
    "sender": "bdat57190@gmail.com",
    "password": "tbqz pmxg ygre zevk",
    "receiver": "datb35054@gmail.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}

_otp_cache = {}
_otp_lock = threading.Lock()

def send_otp_email(username, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL["sender"]
        msg['To'] = GMAIL["receiver"]
        msg['Subject'] = f"🔐 Mã OTP tạo bot {username}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">🔐 XÁC THỰC TẠO BOT</h2>
            <p>Xin chào <b>{username}</b>,</p>
            <p>Mã OTP để tạo bot của bạn là:</p>
            <div style="background: #f0f2f5; padding: 20px; border-radius: 10px; text-align: center; font-size: 36px; font-weight: bold; letter-spacing: 5px; color: #667eea;">
                {otp}
            </div>
            <p style="color: #6b7280; font-size: 14px;">
                ⏰ Mã có hiệu lực trong <b>5 phút</b>.<br>
                ⚠️ Không chia sẻ mã này với bất kỳ ai!
            </p>
            <hr>
            <p style="color: #6b7280; font-size: 12px;">
                Bot Manager • {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(GMAIL["smtp_server"], GMAIL["smtp_port"])
        server.starttls()
        server.login(GMAIL["sender"], GMAIL["password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[OTP] ❌ Lỗi: {e}")
        return False

def generate_otp():
    return str(random.randint(100000, 999999))

# ============================================================
# INIT
# ============================================================

os.makedirs(BOT_MODULES_DIR, exist_ok=True)

def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        pass

def json_load(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def json_save(path, data):
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def init_login():
    if not os.path.exists(LOGIN_FILE):
        json_save(LOGIN_FILE, {"data": [], "dataBot": {}})
        return True
    return True

init_login()
ensure_dir(MULTIBOT_DIR)

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

def get_user_name(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get("displayName", str(uid))
    except:
        return str(uid)

def get_all_bots():
    data = json_load(LOGIN_FILE) or {}
    return data.get("data", [])

def get_bot_by_uid(uid):
    data = json_load(LOGIN_FILE) or {}
    for bot in data.get("data", []):
        if str(bot.get("botIntId")) == str(uid):
            return bot
    return None

def get_bot_by_index(index):
    bots = get_all_bots()
    if 1 <= index <= len(bots):
        return bots[index - 1]
    return None

def get_next_bot_folder():
    i = 1
    while os.path.exists(os.path.join(BOT_MODULES_DIR, f"bot_{i}")):
        i += 1
    return f"bot_{i}"

def save_bot(bot):
    data = json_load(LOGIN_FILE) or {}
    bots = data.get("data", [])
    found = False
    for i, b in enumerate(bots):
        if str(b.get("botIntId")) == str(bot.get("botIntId")):
            bots[i] = bot
            found = True
            break
    if not found:
        bots.append(bot)
    data["data"] = bots
    if "dataBot" not in data:
        data["dataBot"] = {}
    data["dataBot"][str(bot.get("botIntId"))] = bot.get("filePath", "")
    json_save(LOGIN_FILE, data)
    return True

def delete_bot_by_id(bot_id):
    data = json_load(LOGIN_FILE) or {}
    bots = data.get("data", [])
    data["data"] = [b for b in bots if str(b.get("botIntId")) != str(bot_id)]
    if "dataBot" in data:
        data["dataBot"].pop(str(bot_id), None)
    json_save(LOGIN_FILE, data)
    return True

_bot_threads = {}

def start_bot_real(bot):
    try:
        bot_id = bot.get("botIntId")
        folder_name = bot.get("folder", "")
        username = bot.get("username")
        admin_id = bot.get("adminId")  # Lấy adminId
        
        if not folder_name:
            return False, "Bot chưa có folder!"
        
        module_path = f"modules.bots.{folder_name}.bot"
        
        import sys
        bot_path = os.path.join(BASE_DIR, "modules", "bots", folder_name)
        if bot_path not in sys.path:
            sys.path.insert(0, bot_path)
        
        try:
            bot_module = importlib.import_module(module_path)
            if hasattr(bot_module, 'Bot'):
                BotClass = bot_module.Bot
            else:
                return False, "Không tìm thấy class Bot"
        except ImportError as e:
            return False, f"Không tìm thấy module: {e}"
        
        bot_instance = BotClass(
            bot_id=bot_id,
            imei=bot.get("imei"),
            session_cookies=bot.get("sessionCookies"),
            prefix=bot.get("prefix", "!"),
            modules_dir=os.path.join(BASE_DIR, "modules", "bots", folder_name, "modules"),
            admin_id=admin_id  # Truyền adminId vào
        )
        
        _bot_threads[bot_id] = {"bot": bot_instance, "username": username, "running": True}
        bot["status"] = True
        bot["isActived"] = True
        save_bot(bot)
        
        thread = threading.Thread(target=bot_instance.run, daemon=True)
        thread.start()
        
        return True, f"Bot {username} đã chạy!"
    except Exception as e:
        print(f"[Bot] ❌ Lỗi start: {e}")
        return False, str(e)

def stop_bot_real_by_id(bot_id):
    try:
        if bot_id in _bot_threads:
            _bot_threads[bot_id]["running"] = False
            bot = _bot_threads[bot_id].get("bot")
            if bot and hasattr(bot, "stop"):
                bot.stop()
            del _bot_threads[bot_id]
            return True
        return False
    except:
        return False

def is_bot_running(bot_id):
    try:
        if bot_id in _bot_threads:
            return _bot_threads[bot_id].get("running", False)
        return False
    except:
        return False

def get_bot_status_text(bot_id):
    if is_bot_running(bot_id):
        return "🟢 Đang chạy"
    return "🔴 Đã dừng"

def copy_modules_to_bot(bot_folder):
    source = MODULES_DIR
    dest = os.path.join(BOT_MODULES_DIR, bot_folder, "modules")
    
    if os.path.exists(dest):
        shutil.rmtree(dest)
    
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns('bots', '__pycache__', '*.pyc'))
    
    with open(os.path.join(dest, "__init__.py"), "w") as f:
        f.write("# Bot modules\n")
    
    print(f"[Bot] ✅ Copied modules to {bot_folder}")
    return dest

def create_bot_folder(username, imei, cookies, prefix, admin_id):
    folder_name = get_next_bot_folder()
    folder_path = os.path.join(BOT_MODULES_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    copy_modules_to_bot(folder_name)
    
    with open(os.path.join(folder_path, "__init__.py"), "w") as f:
        f.write(f"# Bot {username}\n")
    
    bot_code = '''# modules/bots/__FOLDER__/bot.py
import os
import sys
import json
import time
import importlib
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType

try:
    from asset.config import API_KEY, SECRET_KEY
except:
    API_KEY = "api_key"
    SECRET_KEY = "secret_key"

class Bot(ZaloAPI):
    def __init__(self, bot_id, imei, session_cookies, prefix, modules_dir, admin_id):
        self._imei = imei
        self.imei = imei
        self.bot_id = bot_id
        self.prefix = prefix
        self.admin_id = admin_id  # Lưu admin ID
        self._running = True
        self.modules_dir = modules_dir
        self.commands = {}
        
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        
        try:
            super().__init__(API_KEY, SECRET_KEY, imei, session_cookies)
        except Exception as e:
            if "Phone and password not set" in str(e):
                print(f"[__FOLDER__] ⚠️ Login skipped, using session cookies")
            else:
                print(f"[__FOLDER__] Init error: {e}")
                raise
        
        self._imei = imei
        self.imei = imei
        
        self.load_commands()
        print(f"[__FOLDER__] Bot initialized with prefix: __PREFIX__")
        print(f"[__FOLDER__] Admin ID: {admin_id}")
    
    def load_commands(self):
        try:
            from modules.mybot import Kryzis
            cmds = Kryzis()
            if isinstance(cmds, dict):
                for name, handler in cmds.items():
                    self.commands[name] = {
                        "name": name,
                        "main": handler,
                        "permission": 0,
                        "description": "",
                        "cooldown": 0,
                        "status": True,
                        "alias": []
                    }
                    print(f"[__FOLDER__] ✅ Loaded: {name}")
        except Exception as e:
            print(f"[__FOLDER__] ⚠️ Load mybot error: {e}")
        
        # Load commands from modules
        modules_path = os.path.join(self.modules_dir)
        if os.path.exists(modules_path):
            for filename in os.listdir(modules_path):
                if filename.endswith('.py') and not filename.startswith('__'):
                    mod_name = filename[:-3]
                    if mod_name == "mybot":
                        continue
                    try:
                        module = importlib.import_module(f"modules.{mod_name}")
                        if hasattr(module, 'Kryzis'):
                            cmds = module.Kryzis()
                            if isinstance(cmds, dict):
                                for name, handler in cmds.items():
                                    self.commands[name] = {
                                        "name": name,
                                        "main": handler,
                                        "permission": 0,
                                        "description": "",
                                        "cooldown": 0,
                                        "status": True,
                                        "alias": []
                                    }
                                    print(f"[__FOLDER__] ✅ Loaded: {name}")
                    except Exception as e:
                        print(f"[__FOLDER__] ⚠️ Load {mod_name} error: {e}")
        
        print(f"[__FOLDER__] 📋 Total commands: {len(self.commands)}")
    
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            if message_object.msgType == "chat.sticker":
                return
            c = message_object.content
            if isinstance(c, dict) and "title" in c:
                msg_text = c["title"]
            elif isinstance(c, str):
                msg_text = c
            else:
                return
            
            if not msg_text or not msg_text.strip():
                return
            
            if not msg_text.startswith(self.prefix):
                return
            
            parts = msg_text[len(self.prefix):].strip().split()
            if not parts:
                return
            
            cmd = parts[0].lower()
            
            if cmd in self.commands:
                handler = self.commands[cmd]["main"]
                handler(msg_text, message_object, thread_id, thread_type, author_id, self)
            else:
                self.sendMessage(Message(text=f"❌ Lệnh {cmd} không tồn tại!"), thread_id, thread_type)
            
        except Exception as e:
            print(f"[__FOLDER__] Error: {e}")
    
    def listen(self):
        print(f"[__FOLDER__] 🤖 Bot listening with prefix: {self.prefix}")
        print(f"[__FOLDER__] 📋 Commands: {list(self.commands.keys())}")
        try:
            super().listen()
        except KeyboardInterrupt:
            print(f"[__FOLDER__] 🛑 Bot stopped")
    
    def run(self):
        self.listen()
    
    def stop(self):
        self._running = False
        if hasattr(self, "stopListening"):
            self.stopListening()
    
    def sendMWarning(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"⚠️ {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def sendMFailed(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"❌ {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def sendMSuccess(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"✅ {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def sendMCustom(self, title, icon, text, userId, threadId, type):
        self.sendMessage(Message(text=f"{icon} {title}: {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
        return None
    
    def sendMention(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"@{userId} {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def is_admin(self, user_id):
        """Kiểm tra user có phải admin của bot không"""
        return str(user_id) == str(self.admin_id)
'''
    
    bot_code = bot_code.replace("__FOLDER__", folder_name).replace("__PREFIX__", prefix)
    
    with open(os.path.join(folder_path, "bot.py"), "w", encoding="utf-8") as f:
        f.write(bot_code)
    
    config = {
        "username": username,
        "imei": imei,
        "cookies": cookies,
        "prefix": prefix,
        "admin_id": admin_id,
        "created_at": datetime.now().isoformat()
    }
    with open(os.path.join(folder_path, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    
    return folder_name

# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_mybot(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.strip().split()
        cmdb = f"{PREFIX}mybot"
        
        if len(parts) < 2:
            menu = f"""📋 *QUẢN LÝ BOT*

{cmdb} create <imei> <cookies> - Tạo bot (gửi OTP về Gmail)
{cmdb} verify <otp>            - Xác thực OTP
{cmdb} list       - Danh sách bot
{cmdb} info <index> - Thông tin bot
{cmdb} start <index> - Start bot
{cmdb} stop <index>  - Stop bot
{cmdb} restart <index> - Restart bot
{cmdb} delete <index>  - Xóa bot
{cmdb} prefix <index> <new> - Đổi prefix

💡 *Ví dụ:*
{cmdb} create <imei> '{{"cookie":"value"}}'
{cmdb} verify 123456
{cmdb} start 1"""
            _reply(client, message_object, thread_id, thread_type, menu, sty_info)
            return

        cmd = parts[1].lower()

        if cmd == "create":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} create <imei> <cookies>", sty_err)
                return
            
            imei = parts[2]
            try:
                cookies = json.loads(" ".join(parts[3:]))
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Cookies JSON không hợp lệ!", sty_err)
                return
            
            username = get_user_name(client, author_id)
            admin_id = author_id  # Lưu admin ID
            
            otp = generate_otp()
            with _otp_lock:
                _otp_cache[author_id] = {
                    "otp": otp,
                    "expires": time.time() + 300,
                    "imei": imei,
                    "cookies": cookies,
                    "username": username,
                    "admin_id": admin_id
                }
            
            if send_otp_email(username, otp):
                _reply(client, message_object, thread_id, thread_type,
                    f"✅ Đã gửi mã OTP\n"
                    f"📌 Dùng: {cmdb} verify <OTP>\n"
                    f"⏰ OTP có hiệu lực 5 phút", sty_ok)
            else:
                _reply(client, message_object, thread_id, thread_type,
                    f"❌ Không thể gửi OTP!\n💡 Kiểm tra cấu hình Gmail", sty_err)
            return

        if cmd == "verify":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} verify <otp>", sty_err)
                return
            
            otp = parts[2]
            
            with _otp_lock:
                data = _otp_cache.get(author_id)
                if not data:
                    _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy OTP!", sty_err)
                    return
                
                if time.time() > data["expires"]:
                    del _otp_cache[author_id]
                    _reply(client, message_object, thread_id, thread_type, "❌ OTP đã hết hạn!", sty_err)
                    return
                
                if data["otp"] != otp:
                    _reply(client, message_object, thread_id, thread_type, "❌ Mã OTP không đúng!", sty_err)
                    return
                
                imei = data["imei"]
                cookies = data["cookies"]
                username = data["username"]
                admin_id = data["admin_id"]
                del _otp_cache[author_id]
            
            prefix_list = ["/", ".", "_", "-", ",", ">", "<", ")", "(", "~", "!", "?"]
            prefix = random.choice(prefix_list)
            
            folder_name = create_bot_folder(username, imei, cookies, prefix, admin_id)
            
            botIntId = str(author_id)
            login_file = f"{folder_name}.json"
            
            new_bot = {
                "username": username,
                "login": 24,
                "botIntId": botIntId,
                "imei": imei,
                "prefix": prefix,
                "sessionCookies": cookies,
                "clientBotId": str(author_id),
                "adminId": str(admin_id),  # Thêm admin ID
                "mainBot": False,
                "status": False,
                "isActived": False,
                "approved": True,
                "folder": folder_name,
                "filePath": login_file
            }
            
            data = json_load(LOGIN_FILE) or {}
            if "data" not in data:
                data["data"] = []
            data["data"].append(new_bot)
            if "dataBot" not in data:
                data["dataBot"] = {}
            data["dataBot"][str(author_id)] = login_file
            json_save(LOGIN_FILE, data)
            
            _reply(client, message_object, thread_id, thread_type,
                f"""✅ *TẠO BOT THÀNH CÔNG!*

👤 *Tên:* {username}
🔑 *Prefix:* {prefix}
🆔 *Bot ID:* {botIntId}
👤 *Admin ID:* {admin_id}
📁 *Folder:* {folder_name}

💡 Dùng: {cmdb} start 1 để start bot""", sty_ok)
            return

        if cmd == "list":
            bots = get_all_bots()
            if not bots:
                _reply(client, message_object, thread_id, thread_type, "📋 Chưa có bot nào!", sty_info)
                return
            
            msg = "📋 *DANH SÁCH BOT*\n"
            for i, bot in enumerate(bots, 1):
                status = get_bot_status_text(bot.get("botIntId"))
                msg += f"{i}. {status} *{bot.get('username')}* | {bot.get('prefix')}\n"
                msg += f"   👤 Admin: {bot.get('adminId', 'N/A')}\n"
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        if cmd == "info":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} info <index>", sty_err)
                return
            
            try:
                index = int(parts[2])
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Index phải là số!", sty_err)
                return
            
            bot = get_bot_by_index(index)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy bot {index}", sty_err)
                return
            
            status = get_bot_status_text(bot.get("botIntId"))
            msg = f"""📋 *THÔNG TIN BOT {index}*

👤 *Tên:* {bot.get('username')}
🆔 *Bot ID:* {bot.get('botIntId')}
🔑 *Prefix:* {bot.get('prefix')}
👤 *Admin ID:* {bot.get('adminId', 'N/A')}
📁 *Folder:* {bot.get('folder', 'N/A')}
📊 *Status:* {status}"""
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        if cmd == "start":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} start <index>", sty_err)
                return
            
            try:
                index = int(parts[2])
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Index phải là số!", sty_err)
                return
            
            bot = get_bot_by_index(index)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy bot {index}", sty_err)
                return
            
            success, msg = start_bot_real(bot)
            if success:
                _reply(client, message_object, thread_id, thread_type, f"✅ Bot {bot.get('username')} đã start!", sty_ok)
            else:
                _reply(client, message_object, thread_id, thread_type, f"❌ {msg}", sty_err)
            return

        if cmd == "stop":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} stop <index>", sty_err)
                return
            
            try:
                index = int(parts[2])
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Index phải là số!", sty_err)
                return
            
            bot = get_bot_by_index(index)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy bot {index}", sty_err)
                return
            
            bot_id = bot.get("botIntId")
            stop_bot_real_by_id(bot_id)
            bot["status"] = False
            bot["isActived"] = False
            save_bot(bot)
            _reply(client, message_object, thread_id, thread_type, f"🛑 Bot {bot.get('username')} đã dừng!", sty_warn)
            return

        if cmd == "restart":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} restart <index>", sty_err)
                return
            
            try:
                index = int(parts[2])
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Index phải là số!", sty_err)
                return
            
            bot = get_bot_by_index(index)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy bot {index}", sty_err)
                return
            
            bot_id = bot.get("botIntId")
            stop_bot_real_by_id(bot_id)
            time.sleep(0.5)
            success, msg = start_bot_real(bot)
            if success:
                _reply(client, message_object, thread_id, thread_type, f"🔄 Bot {bot.get('username')} đã restart!", sty_ok)
            else:
                _reply(client, message_object, thread_id, thread_type, f"❌ {msg}", sty_err)
            return

        if cmd == "delete":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} delete <index>", sty_err)
                return
            
            try:
                index = int(parts[2])
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Index phải là số!", sty_err)
                return
            
            bot = get_bot_by_index(index)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy bot {index}", sty_err)
                return
            
            bot_id = bot.get("botIntId")
            stop_bot_real_by_id(bot_id)
            
            folder_name = bot.get("folder")
            if folder_name:
                folder_path = os.path.join(BOT_MODULES_DIR, folder_name)
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
            
            delete_bot_by_id(bot_id)
            _reply(client, message_object, thread_id, thread_type, f"🗑️ Đã xóa bot {bot.get('username')}", sty_ok)
            return

        if cmd == "prefix":
            if len(parts) < 4:
                _reply(client, message_object, thread_id, thread_type, f"❌ Usage: {cmdb} prefix <index> <new_prefix>", sty_err)
                return
            
            try:
                index = int(parts[2])
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Index phải là số!", sty_err)
                return
            
            new_prefix = parts[3]
            bot = get_bot_by_index(index)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy bot {index}", sty_err)
                return
            
            old_prefix = bot.get("prefix")
            bot["prefix"] = new_prefix
            save_bot(bot)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đổi prefix: {old_prefix} → {new_prefix}", sty_ok)
            return

        _reply(client, message_object, thread_id, thread_type, f"❌ Lệnh {cmd} không hỗ trợ!\n💡 {cmdb} để xem hướng dẫn", sty_err)

    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ Lỗi: {str(e)[:100]}", sty_err)

def Kryzis():
    return {'mybot': handle_mybot}