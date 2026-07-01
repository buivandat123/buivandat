# modules/mybot.py
# -*- coding: utf-8 -*-
import os
import json
import time
import random
import re
import threading
import subprocess
import socket
import importlib
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from zlapi import ZaloAPI

des = {
    'version': "2.0.0",
    'credits': "Kryzis",
    'description': "Quản lý bot đa người dùng",
    'power': "Quản trị viên và thành viên"
}

PREFIX = "."
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIN_FILE = os.path.join(BASE_DIR, "asset", "config", "login.json")
MULTIBOT_DIR = os.path.join(BASE_DIR, "asset", "config", "multibot")
WEB_PORT = 5000
_tunnel_url = None
_tunnel_process = None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def check_cloudflared():
    try:
        result = subprocess.run(["cloudflared", "--version"], capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False

def get_cloudflared_path():
    paths = [
        "/data/data/com.termux/files/usr/bin/cloudflared",
        "/usr/local/bin/cloudflared",
        "/usr/bin/cloudflared",
        "cloudflared"
    ]
    for path in paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, timeout=2)
            if result.returncode == 0:
                return path
        except:
            continue
    return None

def start_cloudflare_tunnel():
    global _tunnel_url, _tunnel_process
    if _tunnel_url:
        return _tunnel_url
    if not check_cloudflared():
        return None
    cloudflared_path = get_cloudflared_path()
    if not cloudflared_path:
        return None
    try:
        _tunnel_process = subprocess.Popen(
            [cloudflared_path, "tunnel", "--url", f"http://localhost:{WEB_PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in iter(_tunnel_process.stdout.readline, ''):
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                _tunnel_url = match.group(0)
                return _tunnel_url
        return None
    except:
        return None

def get_public_url():
    global _tunnel_url
    if not _tunnel_url:
        _tunnel_url = start_cloudflare_tunnel()
    if _tunnel_url:
        return _tunnel_url
    
    # Đọc từ file public_url.txt nếu có
    public_file = os.path.join(BASE_DIR, "public_url.txt")
    if os.path.exists(public_file):
        try:
            with open(public_file, "r") as f:
                url = f.read().strip()
                if url:
                    _tunnel_url = url
                    return _tunnel_url
        except:
            pass
    
    return f"http://{get_local_ip()}:{WEB_PORT}"

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
    data = json_load(LOGIN_FILE)
    if "data" not in data:
        data["data"] = []
    if "dataBot" not in data:
        data["dataBot"] = {}
    json_save(LOGIN_FILE, data)
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

def get_next_login_file():
    i = 1
    while os.path.exists(os.path.join(MULTIBOT_DIR, f"{i}-login.json")):
        i += 1
    return f"{i}-login.json"

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

def load_all_commands():
    commands = {}
    modules_dir = "modules"
    if not os.path.exists(modules_dir):
        return commands
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'modules.{module_name}')
                if hasattr(module, 'Kryzis'):
                    kryzis_func = getattr(module, 'Kryzis')
                    if callable(kryzis_func):
                        cmds = kryzis_func()
                        if isinstance(cmds, dict):
                            for cmd_name, handler in cmds.items():
                                commands[cmd_name] = {
                                    "name": cmd_name,
                                    "main": handler,
                                    "permission": 0,
                                    "description": "",
                                    "cooldown": 0,
                                    "status": True,
                                    "alias": []
                                }
            except:
                pass
    return commands

def start_bot_real(bot):
    try:
        from asset.config import API_KEY, SECRET_KEY
        
        bot_id = bot.get("botIntId")
        imei = bot.get("imei")
        session_cookies = bot.get("sessionCookies")
        prefix = bot.get("prefix", "!")
        username = bot.get("username")
        
        if not imei or not session_cookies:
            return False, "Thiếu IMEI hoặc Cookies!"
        
        stop_bot_real_by_id(bot_id)
        time.sleep(0.5)
        
        class SimpleBot(ZaloAPI):
            def __init__(self, imei, session_cookies, prefix):
                self._imei = imei
                self.imei = imei
                self.prefix = prefix
                self._bot_enabled = True
                self.listening = True
                self.uid = imei
                self.username = username
                self.commands = {}
                try:
                    super().__init__(API_KEY, SECRET_KEY, imei, session_cookies)
                except Exception as e:
                    print(f"[SimpleBot] ⚠️ Init error: {e}")
                    raise
                self.commands = load_all_commands()
                print(f"[SimpleBot] 📋 Total commands: {len(self.commands)}")
            
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
                    print(f"[SimpleBot] ❌ Error: {e}")
            
            def listen(self):
                print(f"[SimpleBot] 🤖 Bot running with prefix: {self.prefix}")
                self.listening = True
                try:
                    super().listen()
                except KeyboardInterrupt:
                    print("\n[SimpleBot] 🛑 Stopped")
                finally:
                    self.listening = False
            
            def stopListening(self):
                self.listening = False
                self._bot_enabled = False
            
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
            
            def deleteMessage(self, *args):
                pass
            
            def sendImage(self, *args, **kwargs):
                return None
            
            def undoMessage(self, *args):
                pass
            
            def uploadImage(self, *args):
                return {}
            
            def userName(self, uid):
                return str(uid)
            
            def randomInt(self):
                return random.randint(100000, 999999)
        
        bot_instance = SimpleBot(imei, session_cookies, prefix)
        _bot_threads[bot_id] = {"bot": bot_instance, "username": username}
        bot["status"] = True
        bot["isActived"] = True
        save_bot(bot)
        thread = threading.Thread(target=bot_instance.listen, daemon=True)
        thread.start()
        return True, f"Bot đã chạy với {len(bot_instance.commands)} lệnh!"
    except Exception as e:
        print(f"[MyBot] ❌ Lỗi start bot: {e}")
        return False, str(e)

def stop_bot_real_by_id(bot_id):
    try:
        if bot_id in _bot_threads:
            bot = _bot_threads[bot_id].get("bot")
            if bot and hasattr(bot, "stopListening"):
                bot.stopListening()
            del _bot_threads[bot_id]
            return True
        return False
    except:
        return False

def is_bot_running(bot_id):
    try:
        if bot_id in _bot_threads:
            bot = _bot_threads[bot_id].get("bot")
            if bot and hasattr(bot, "listening"):
                return bot.listening
        return False
    except:
        return False

def handle_mybot(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.strip().split()
        cmdb = f"{PREFIX}mybot"
        
        if len(parts) < 2:
            menu = f"""📋 *QUẢN LÝ BOT*

1. *Create applications*
{cmdb} create IMEI Session Cookies: Create with imei and cookies
{cmdb} create qr: Create with QR Code

2. *Manager your applications:*
{cmdb} list: All bots
{cmdb} info: Get Info
{cmdb} restart: Restart your BOT
{cmdb} stop: Stop your BOT
{cmdb} prefix: Set bot prefix
{cmdb} server: Get appServer
{cmdb} login: Set login type

3. *Management for main*
type {cmdb} manager."""
            _reply(client, message_object, thread_id, thread_type, menu, sty_info)
            return

        cmd = parts[1].lower()

        if cmd == "server":
            web_url = get_public_url()
            _reply(client, message_object, thread_id, thread_type, f"🔗 {web_url}", sty_ok)
            return

        if cmd == "info":
            bot = get_bot_by_uid(author_id)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, "🚦 Bạn chưa có bot!", sty_warn)
                return
            web_url = get_public_url()
            running = is_bot_running(bot.get("botIntId"))
            info = f"""📋 *{bot.get('username', 'Unknown')}*
🆔 {bot.get('botIntId')}
📊 {'✅ Đang chạy' if running else '❌ Đã dừng'}
🚀 {bot.get('prefix', '?')}
🔗 {web_url}
👤 {bot.get('botAccount', 'N/A')}
🔑 {bot.get('botPassword', 'N/A')}"""
            _reply(client, message_object, thread_id, thread_type, info, sty_info)
            return

        if cmd == "list":
            bots = get_all_bots()
            if not bots:
                _reply(client, message_object, thread_id, thread_type, "📋 Chưa có bot nào!", sty_info)
                return
            msg = "📋 *DANH SÁCH BOT*\n"
            for i, bot in enumerate(bots, 1):
                running = is_bot_running(bot.get("botIntId"))
                status = "🟢" if running else "🔴"
                msg += f"{i}. {status} *{bot.get('username', 'Unknown')}* | {bot.get('prefix', '?')}\n"
                msg += f"   👤 {bot.get('botAccount', 'N/A')} | 🔑 {bot.get('botPassword', 'N/A')}\n"
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        if cmd == "create":
            if len(parts) < 4:
                _reply(client, message_object, thread_id, thread_type,
                    f"""📋 *TẠO BOT*
{cmdb} create [imei] [cookies]
💡 {cmdb} create 857b9c28-39b6-432b-a073-87be165e8692 '{{"cookie":"value"}}'""", sty_info)
                return
            
            uidFrom = author_id
            imei = parts[2]
            try:
                cookies = json.loads(" ".join(parts[3:]))
            except:
                _reply(client, message_object, thread_id, thread_type, "❌ Cookies không hợp lệ!", sty_err)
                return
            
            if get_bot_by_uid(uidFrom):
                _reply(client, message_object, thread_id, thread_type, "🚦 Bạn đã có bot!", sty_warn)
                return
            
            username = get_user_name(client, uidFrom)
            prefix_list = ["/", ".", "_", "-", ",", ">", "<", ")", "(", "~", "!", "?"]
            prefix = random.choice(prefix_list)
            botAccount = username.lower().replace(" ", "")[:10] + str(random.randint(10, 99))
            botPassword = str(random.randint(100000, 999999))
            
            login_file = get_next_login_file()
            login_path = os.path.join(MULTIBOT_DIR, login_file)
            
            new_bot = {
                "username": username,
                "login": 24,
                "botIntId": str(uidFrom),
                "imei": imei,
                "prefix": prefix,
                "sessionCookies": cookies,
                "clientBotId": str(uidFrom),
                "mainBot": False,
                "status": False,
                "isActived": False,
                "approved": True,
                "botAccount": botAccount,
                "botPassword": botPassword,
                "activedTime": None,
                "expiredTime": None,
                "filePath": login_file
            }
            
            with open(login_path, "w", encoding="utf-8") as f:
                json.dump([new_bot, {"userClientId": str(uidFrom)}], f, ensure_ascii=False, indent=4)
            
            data = json_load(LOGIN_FILE) or {}
            if "data" not in data:
                data["data"] = []
            data["data"].append(new_bot)
            if "dataBot" not in data:
                data["dataBot"] = {}
            data["dataBot"][str(uidFrom)] = login_file
            json_save(LOGIN_FILE, data)
            
            # Lấy link public từ file hoặc tunnel
            web_url = get_public_url()
            bot_link = f"{web_url}/bot/{uidFrom}"
            
            msg = f"""✅ *TẠO BOT THÀNH CÔNG!*

👤 *Username:* {username}
🔑 *Prefix:* {prefix}
👤 *Account:* {botAccount}
🔐 *Password:* {botPassword}
🔗 *Link Bot:* {bot_link}

💡 Dùng: {cmdb} start 1 30d để start bot
🔐 Login Bot: {bot_link}/login"""
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_ok)
            return

        if cmd == "start":
            if len(parts) < 4:
                _reply(client, message_object, thread_id, thread_type, f"📋 {cmdb} start [index] [time]\n💡 {cmdb} start 1 30d", sty_info)
                return
            
            try:
                index = int(parts[2]) - 1
                time_expr = parts[3]
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type, "🚦 Không tìm thấy bot!", sty_warn)
                    return
                
                now = datetime.now()
                if time_expr.lower() == "vinhvien":
                    expired = "Vĩnh viễn"
                elif time_expr.endswith('d'):
                    days = int(time_expr[:-1])
                    expired = (now + timedelta(days=days)).strftime('%d/%m/%Y')
                elif time_expr.endswith('h'):
                    hours = int(time_expr[:-1])
                    expired = (now + timedelta(hours=hours)).strftime('%d/%m/%Y %H:%M')
                else:
                    _reply(client, message_object, thread_id, thread_type, "❌ Thời gian không hợp lệ! Dùng: 1d, 5h, 30m", sty_err)
                    return
                
                bot["status"] = True
                bot["isActived"] = True
                bot["activedTime"] = now.strftime("%H:%M:%S-%d/%m/%Y")
                bot["expiredTime"] = expired
                save_bot(bot)
                
                success, msg = start_bot_real(bot)
                if success:
                    _reply(client, message_object, thread_id, thread_type, f"✅ Đã start {bot.get('username')}\n⏰ {expired}", sty_ok)
                else:
                    _reply(client, message_object, thread_id, thread_type, f"⚠️ {msg}", sty_warn)
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:80]}", sty_err)
            return

        if cmd == "stop":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"📋 {cmdb} stop [index]", sty_info)
                return
            try:
                index = int(parts[2]) - 1
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type, "🚦 Không tìm thấy bot!", sty_warn)
                    return
                bot_id = bot.get("botIntId")
                stop_bot_real_by_id(bot_id)
                bot["status"] = False
                bot["isActived"] = False
                save_bot(bot)
                _reply(client, message_object, thread_id, thread_type, f"🛑 Đã stop {bot.get('username')}", sty_warn)
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:80]}", sty_err)
            return

        if cmd == "restart":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"📋 {cmdb} restart [index]", sty_info)
                return
            try:
                index = int(parts[2]) - 1
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type, "🚦 Không tìm thấy bot!", sty_warn)
                    return
                bot_id = bot.get("botIntId")
                stop_bot_real_by_id(bot_id)
                time.sleep(0.5)
                bot["status"] = True
                bot["isActived"] = True
                save_bot(bot)
                success, msg = start_bot_real(bot)
                if success:
                    _reply(client, message_object, thread_id, thread_type, f"🔄 Đã restart {bot.get('username')}", sty_ok)
                else:
                    _reply(client, message_object, thread_id, thread_type, f"⚠️ {msg}", sty_warn)
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:80]}", sty_err)
            return

        if cmd == "delete":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"📋 {cmdb} delete [index]", sty_info)
                return
            try:
                index = int(parts[2]) - 1
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type, "🚦 Không tìm thấy bot!", sty_warn)
                    return
                bot_id = bot.get("botIntId")
                stop_bot_real_by_id(bot_id)
                data = json_load(LOGIN_FILE) or {}
                dataBot = data.get("dataBot", {})
                login_file = dataBot.get(str(bot_id))
                if login_file:
                    login_path = os.path.join(MULTIBOT_DIR, login_file)
                    if os.path.exists(login_path):
                        os.remove(login_path)
                delete_bot_by_id(bot_id)
                _reply(client, message_object, thread_id, thread_type, f"🗑️ Đã xóa {bot.get('username')}", sty_ok)
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:80]}", sty_err)
            return

        if cmd == "prefix":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, f"📋 {cmdb} prefix [new_prefix]", sty_info)
                return
            new_prefix = parts[2]
            bot = get_bot_by_uid(author_id)
            if not bot:
                _reply(client, message_object, thread_id, thread_type, "🚦 Bạn chưa có bot!", sty_warn)
                return
            old_prefix = bot.get("prefix", "?")
            bot["prefix"] = new_prefix
            save_bot(bot)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đổi prefix: {old_prefix} → {new_prefix}", sty_ok)
            return

        if cmd == "login":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type, "Set a login type: web or pc", sty_err)
                return
            loginType = parts[2].lower()
            if loginType not in ("web", "pc"):
                _reply(client, message_object, thread_id, thread_type, "Type support: web and pc", sty_err)
                return
            _reply(client, message_object, thread_id, thread_type, f"✅ Updated login type: {loginType.upper()}", sty_ok)
            return

        if cmd == "manager":
            _reply(client, message_object, thread_id, thread_type,
                f"""{cmdb} Manager [Server]
    Set GROUP to get login status: {cmdb} group set
    Set send login status: {cmdb} group notify
    Delete userBot: {cmdb} delete [Target]
    Main can target a BOT with mentions or choose index of that BOT""", sty_info)
            return

        _reply(client, message_object, thread_id, thread_type, f"❌ Lệnh {cmd} không hỗ trợ!\n💡 {cmdb} để xem hướng dẫn", sty_err)

    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:80]}", sty_err)

def Kryzis():
    return {'mybot': handle_mybot}