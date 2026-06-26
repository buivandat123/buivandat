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
import requests
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle

des = {
    'version': "2.0.0",
    'credits': "Kryzis",
    'description': "Quản lý bot đa người dùng",
    'power': "Quản trị viên và thành viên"
}

PREFIX = "."
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mainLogin = os.path.join(BASE_DIR, "asset", "config", "main_login.json")
MULTIBOT_DIR = os.path.join(BASE_DIR, "asset", "config", "multibot")

# ============================================================
# WEB SERVER CONFIG - CLOUDFLARE TUNNEL
# ============================================================

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
        print("[Cloudflare] ⚠️ cloudflared chưa được cài đặt!")
        print("[Cloudflare] 📌 Cài đặt: pkg install cloudflared")
        return None
    
    cloudflared_path = get_cloudflared_path()
    if not cloudflared_path:
        print("[Cloudflare] ❌ Không tìm thấy cloudflared!")
        return None
    
    try:
        print(f"[Cloudflare] 🚀 Đang khởi động tunnel...")
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
                print(f"[Cloudflare] ✅ Tunnel URL: {_tunnel_url}")
                return _tunnel_url
            
            line_lower = line.lower()
            if "error" in line_lower or "failed" in line_lower:
                print(f"[Cloudflare] ⚠️ {line.strip()}")
        
        return None
        
    except Exception as e:
        print(f"[Cloudflare] ❌ Lỗi khởi động tunnel: {e}")
        return None

def get_public_url():
    global _tunnel_url
    if not _tunnel_url:
        _tunnel_url = start_cloudflare_tunnel()
    if _tunnel_url:
        return _tunnel_url
    ip = get_local_ip()
    return f"http://{ip}:{WEB_PORT}"

# ============================================================
# INIT
# ============================================================

def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        pass

def jsonLoader(filename):
    if not os.path.exists(filename):
        try:
            ensure_dir(os.path.dirname(filename))
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        except:
            pass
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def saveJson(filename, data):
    try:
        ensure_dir(os.path.dirname(filename))
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def init_main_login():
    if not os.path.exists(mainLogin):
        ensure_dir(os.path.dirname(mainLogin))
        default_data = {
            "data": [],
            "dataBot": {}
        }
        saveJson(mainLogin, default_data)
        return True
    try:
        data = jsonLoader(mainLogin)
        if not isinstance(data, dict):
            data = {}
        if "data" not in data:
            data["data"] = []
        if "dataBot" not in data:
            data["dataBot"] = {}
        saveJson(mainLogin, data)
        return True
    except:
        return False

init_main_login()
ensure_dir(MULTIBOT_DIR)

# ============================================================
# STYLE - FONT NHỎ
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

def get_user_name(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get("displayName", str(uid))
    except:
        return str(uid)

def get_all_bots():
    data = jsonLoader(mainLogin) or {}
    return data.get("data", [])

def get_bot_by_uid(uid):
    data = jsonLoader(mainLogin) or {}
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
    data = jsonLoader(mainLogin) or {}
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
    saveJson(mainLogin, data)
    return True

def delete_bot_by_id(bot_id):
    data = jsonLoader(mainLogin) or {}
    bots = data.get("data", [])
    data["data"] = [b for b in bots if str(b.get("botIntId")) != str(bot_id)]
    saveJson(mainLogin, data)
    return True

# ============================================================
# COMMAND HANDLERS
# ============================================================

def handle_mybot(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.strip().split()
        cmdb = f"{PREFIX}mybot"
        
        if len(parts) < 2:
            _reply(client, message_object, thread_id, thread_type,
                f"""📋 QUẢN LÝ BOT

{cmdb} create [imei] [cookies] - Tạo bot mới
{cmdb} list                   - Danh sách bot
{cmdb} info                   - Thông tin bot của bạn
{cmdb} start [index] [time]   - Start bot (admin)
{cmdb} stop [index]           - Stop bot (admin)
{cmdb} restart [index]        - Restart bot (admin)
{cmdb} delete [index]         - Xóa bot (admin)
{cmdb} prefix [new]           - Đổi prefix
{cmdb} server                 - Xem server
{cmdb} login [web/pc]         - Set login type

💡 Time: 1d, 5h, 30m, 7d, 30d""", sty_info)
            return

        cmd = parts[1].lower()

        # ===== SERVER =====
        if cmd == "server":
            web_url = get_public_url()
            _reply(client, message_object, thread_id, thread_type,
                f"🔗 {web_url}", sty_ok)
            return

        # ===== LOGIN =====
        if cmd == "login":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type,
                    "Set a login type: web or pc", sty_err)
                return

            loginType = parts[2].lower()
            if loginType not in ("web", "pc"):
                _reply(client, message_object, thread_id, thread_type,
                    "Type support: web and pc", sty_err)
                return

            _reply(client, message_object, thread_id, thread_type,
                f"✅ Updated login type: {loginType.upper()}", sty_ok)
            return

        # ===== INFO =====
        if cmd == "info":
            bot = get_bot_by_uid(author_id)
            if not bot:
                _reply(client, message_object, thread_id, thread_type,
                    "🚦 Bạn chưa có bot!", sty_warn)
                return
            
            web_url = get_public_url()
            # Lấy tên không dấu để làm subdomain
            name_raw = bot.get('username', 'Unknown')
            name_slug = re.sub(r'[^a-zA-Z0-9]', '', name_raw.lower())
            custom_url = f"https://{name_slug}.trycloudflare.com" if name_slug else web_url
            
            info = f"""📋 {bot.get('username', 'Unknown')}
🆔 {bot.get('botIntId')}
📊 {'✅' if bot.get('status') else '❌'}
🚀 {bot.get('prefix', '?')}
🔗 {custom_url}"""
            _reply(client, message_object, thread_id, thread_type, info, sty_info)
            return

        # ===== LIST =====
        if cmd == "list":
            bots = get_all_bots()
            if not bots:
                _reply(client, message_object, thread_id, thread_type,
                    "📋 Chưa có bot nào!", sty_info)
                return
            
            msg = "📋 DANH SÁCH BOT\n"
            for i, bot in enumerate(bots, 1):
                status = "✅" if bot.get("status") else "❌"
                running = "🟢" if bot.get("isActived") else "🔴"
                msg += f"{i}. {status}{running} {bot.get('username', 'Unknown')} | {bot.get('prefix', '?')}\n"
            
            _reply(client, message_object, thread_id, thread_type, msg, sty_info)
            return

        # ===== CREATE =====
        if cmd == "create":
            if len(parts) < 4:
                _reply(client, message_object, thread_id, thread_type,
                    f"""📋 TẠO BOT

{cmdb} create [imei] [cookies]

💡 {cmdb} create 857b9c28-39b6-432b-a073-87be165e8692 [{{\"cookie\":\"value\"}}]""", sty_info)
                return
            
            uidFrom = author_id
            imei = parts[2]
            
            try:
                cookies = json.loads(" ".join(parts[3:]))
            except:
                _reply(client, message_object, thread_id, thread_type,
                    "❌ Cookies không hợp lệ!", sty_err)
                return
            
            if get_bot_by_uid(uidFrom):
                _reply(client, message_object, thread_id, thread_type,
                    "🚦 Bạn đã có bot!", sty_warn)
                return
            
            username = get_user_name(client, uidFrom)
            prefix_list = ["/", ".", "_", "-", ",", ">", "<", ")", "(", "~", "!", "?"]
            prefix = random.choice(prefix_list)
            botAccount = username.lower().replace(" ", "") + str(random.randint(10, 99))
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
                "approved": False,
                "botAccount": botAccount,
                "botPassword": botPassword,
                "activedTime": None,
                "expiredTime": None
            }
            
            with open(login_path, "w", encoding="utf-8") as f:
                json.dump([new_bot, {"userClientId": str(uidFrom)}], f, ensure_ascii=False, indent=4)
            
            data = jsonLoader(mainLogin) or {}
            dataBot = data.get("dataBot", {})
            dataBot[str(uidFrom)] = login_file
            data["dataBot"] = dataBot
            
            if "data" not in data:
                data["data"] = []
            data["data"].append(new_bot)
            
            saveJson(mainLogin, data)
            
            web_url = get_public_url()
            
            # Tạo link dạng https://<tên>.trycloudflare.com
            name_slug = re.sub(r'[^a-zA-Z0-9]', '', username.lower())
            if name_slug:
                custom_url = f"https://{name_slug}.trycloudflare.com"
            else:
                custom_url = web_url
            
            # ✅ GỌN GÀNG - KHÔNG ID, KHÔNG NGÀY
            msg = f"""✅ TẠO BOT THÀNH CÔNG!
👤 {username}
🚀 {prefix}
🔗 {custom_url}
👤 {botAccount}
🔑 {botPassword}"""
            
            try:
                client.sendMessage(Message(text=msg, style=sty_ok(msg)), author_id, ThreadType.USER)
            except:
                _reply(client, message_object, thread_id, thread_type, msg, sty_ok)
            
            return

        # ===== START =====
        if cmd == "start":
            if len(parts) < 4:
                _reply(client, message_object, thread_id, thread_type,
                    f"📋 {cmdb} start [index] [time]\n💡 {cmdb} start 1 30d", sty_info)
                return
            
            try:
                index = int(parts[2]) - 1
                time_expr = parts[3]
                
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type,
                        "🚦 Không tìm thấy bot!", sty_warn)
                    return
                
                if not bot.get("approved", False):
                    _reply(client, message_object, thread_id, thread_type,
                        "🚦 Bot chưa được duyệt!", sty_warn)
                    return
                
                now = datetime.now()
                if time_expr.lower() == "vinhvien":
                    expired = "Vĩnh viễn"
                else:
                    if time_expr.endswith('d'):
                        days = int(time_expr[:-1])
                        expired = (now + timedelta(days=days)).strftime('%d/%m/%Y')
                    elif time_expr.endswith('h'):
                        hours = int(time_expr[:-1])
                        expired = (now + timedelta(hours=hours)).strftime('%d/%m/%Y %H:%M')
                    else:
                        _reply(client, message_object, thread_id, thread_type,
                            "❌ Thời gian không hợp lệ! Dùng: 1d, 5h, 30m", sty_err)
                        return
                
                bot["status"] = True
                bot["isActived"] = True
                bot["activedTime"] = now.strftime("%H:%M:%S-%d/%m/%Y")
                bot["expiredTime"] = expired
                
                save_bot(bot)
                
                _reply(client, message_object, thread_id, thread_type,
                    f"✅ Đã start {bot.get('username')}\n⏰ {expired}", sty_ok)
                
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type,
                    f"❌ {str(e)[:80]}", sty_err)
            return

        # ===== STOP =====
        if cmd == "stop":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type,
                    f"📋 {cmdb} stop [index]", sty_info)
                return
            
            try:
                index = int(parts[2]) - 1
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type,
                        "🚦 Không tìm thấy bot!", sty_warn)
                    return
                
                bot["status"] = False
                bot["isActived"] = False
                save_bot(bot)
                
                _reply(client, message_object, thread_id, thread_type,
                    f"🛑 Đã stop {bot.get('username')}", sty_warn)
                
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type,
                    f"❌ {str(e)[:80]}", sty_err)
            return

        # ===== RESTART =====
        if cmd == "restart":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type,
                    f"📋 {cmdb} restart [index]", sty_info)
                return
            
            try:
                index = int(parts[2]) - 1
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type,
                        "🚦 Không tìm thấy bot!", sty_warn)
                    return
                
                bot["status"] = True
                bot["isActived"] = True
                save_bot(bot)
                
                _reply(client, message_object, thread_id, thread_type,
                    f"🔄 Đã restart {bot.get('username')}", sty_ok)
                
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type,
                    f"❌ {str(e)[:80]}", sty_err)
            return

        # ===== DELETE =====
        if cmd == "delete":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type,
                    f"📋 {cmdb} delete [index]", sty_info)
                return
            
            try:
                index = int(parts[2]) - 1
                bot = get_bot_by_index(index)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type,
                        "🚦 Không tìm thấy bot!", sty_warn)
                    return
                
                bot_id = bot.get("botIntId")
                
                data = jsonLoader(mainLogin) or {}
                dataBot = data.get("dataBot", {})
                login_file = dataBot.get(str(bot_id))
                if login_file:
                    login_path = os.path.join(MULTIBOT_DIR, login_file)
                    if os.path.exists(login_path):
                        os.remove(login_path)
                    del dataBot[str(bot_id)]
                    data["dataBot"] = dataBot
                    saveJson(mainLogin, data)
                
                delete_bot_by_id(bot_id)
                
                _reply(client, message_object, thread_id, thread_type,
                    f"🗑️ Đã xóa {bot.get('username')}", sty_ok)
                
            except Exception as e:
                _reply(client, message_object, thread_id, thread_type,
                    f"❌ {str(e)[:80]}", sty_err)
            return

        # ===== PREFIX =====
        if cmd == "prefix":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type,
                    f"📋 {cmdb} prefix [new_prefix]", sty_info)
                return
            
            new_prefix = parts[2]
            bot = get_bot_by_uid(author_id)
            if not bot:
                _reply(client, message_object, thread_id, thread_type,
                    "🚦 Bạn chưa có bot!", sty_warn)
                return
            
            old_prefix = bot.get("prefix", "?")
            bot["prefix"] = new_prefix
            save_bot(bot)
            
            _reply(client, message_object, thread_id, thread_type,
                f"✅ Đổi prefix: {old_prefix} → {new_prefix}", sty_ok)
            return

        # ===== UNKNOWN =====
        _reply(client, message_object, thread_id, thread_type,
            f"❌ Lệnh {cmd} không hỗ trợ!\n💡 {cmdb} để xem hướng dẫn", sty_err)

    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
            f"❌ {str(e)[:80]}", sty_err)

# ============================================================
# LOAD
# ============================================================

def Kryzis():
    return {'mybot': handle_mybot}