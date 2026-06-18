# modules/mybot.py
# -*- coding: utf-8 -*-
import os
import json
import time
import threading
import traceback
from datetime import datetime
from zlapi import ZaloAPI, ThreadType
from zlapi.models import Message, Mention
from zlapi._exception import ZaloLoginError
from main import SubBotManager

des = {
    'version': "1.0.0",
    'credits': "TXA x ",
    'description': "Quản lý và tạo bot con chạy cùng bot mẹ",
    'power': "Admin"
}

BOTS_DIR = "modules/bots"
CACHE_DIR = "modules/cache/mybot"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(BOTS_DIR, exist_ok=True)

def is_admin(author_id, client):
    try:
        from LIGHT import check_is_admin
        return check_is_admin(author_id)
    except:
        pass
    try:
        with open("asset/seting.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            owner = str(data.get("admin", ""))
            admins = [str(x) for x in data.get("adm", [])]
            return str(author_id) == owner or str(author_id) in admins
    except:
        return False

def _reply(client, text, message_object, thread_id, thread_type):
    client.replyMessage(Message(text=text), message_object, thread_id, thread_type, ttl=120000)

def generate_run_py(folder):
    run_py_content = """# -*- coding: utf-8 -*-
import sys
import os
import json

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

# Import canvas as requested by user
from modules.canvas import *

from main import MainBot
import asset.config

# Load config
with open(os.path.join(current_dir, "bot_config.json"), "r", encoding="utf-8") as f:
    cfg = json.load(f)

# Patch configuration
asset.config.IMEI = cfg.get("IMEI")
asset.config.SESSION_COOKIES = cfg.get("SESSION_COOKIES")
asset.config.PREFIX = cfg.get("PREFIX")
asset.config.ADMIN = cfg.get("ADMIN")

# Start client
try:
    client = MainBot(asset.config.API_KEY, asset.config.SECRET_KEY, asset.config.IMEI, asset.config.SESSION_COOKIES)
    client.settings["prefix"] = asset.config.PREFIX
    client.ADMIN = str(asset.config.ADMIN)
    client.listen()
except KeyboardInterrupt:
    print("\\n👋 Đang dừng bot con sạch sẽ (Ctrl+C)... Hẹn gặp lại!")
    sys.exit(0)
"""
    with open(os.path.join(folder, "run.py"), "w", encoding="utf-8") as f:
        f.write(run_py_content)

def login_and_create_subbot(client, thread_id, thread_type, message_object, bot_name, bot_prefix, admin_id):
    qr_file_path = os.path.join(CACHE_DIR, f"qr_login_{bot_name}_{int(time.time())}.png")
    temp_client = None
    
    init_msg = None
    qr_message_result = [None]

    def delete_msg(msg_res):
        if msg_res and hasattr(msg_res, "msgId"):
            try:
                cli_msg_id = getattr(msg_res, "cliMsgId", str(int(time.time() * 1000)))
                client.undoMessage(msgId=msg_res.msgId, cliMsgId=cli_msg_id, thread_id=thread_id, thread_type=thread_type)
            except:
                pass

    try:
        temp_client = ZaloAPI(phone=None, password=None, imei=None, auto_login=False)
        
        init_msg = _reply(client, "⏳ Đang khởi tạo QR đăng nhập cho bot con...", message_object, thread_id, thread_type)
        
        def send_qr_to_user(path_to_qr):
            if os.path.exists(path_to_qr):
                delete_msg(init_msg)
                qr_message_result[0] = client.sendLocalImage(
                    imagePath=path_to_qr,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    message=Message(text=f"🔐 Hãy dùng Zalo quét mã QR này trong 100 giây để kích hoạt bot con '{bot_name}'"),
                    ttl=100000
                )
        
        def on_scanned_callback(display_name):
            delete_msg(qr_message_result[0])
            _reply(client, f"✔ Mã QR đã được quét bởi: {display_name}.\nVui lòng xác nhận đăng nhập trên điện thoại của bạn.", message_object, thread_id, thread_type)

        temp_client.loginWithQR(
            qr_path=qr_file_path,
            on_qr_generated=send_qr_to_user,
            on_scanned=on_scanned_callback
        )
        
        if temp_client.isLoggedIn():
            imei = temp_client._state.user_imei
            cookies = temp_client.getSession()
            
            # Create bot folder
            folder = os.path.join(BOTS_DIR, bot_name)
            os.makedirs(folder, exist_ok=True)
            
            # Save config
            cfg = {
                "IMEI": imei,
                "SESSION_COOKIES": cookies,
                "PREFIX": bot_prefix,
                "ADMIN": admin_id,
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            with open(os.path.join(folder, "bot_config.json"), "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            
            # Generate run.py
            generate_run_py(folder)
            
            _reply(client, f"✅ Đã tạo cấu hình cho bot con '{bot_name}' thành công! Đang tiến hành bật bot...", message_object, thread_id, thread_type)
            
            # Start bot con
            success, result = SubBotManager.start(bot_name, {"folder": folder})
            if success:
                _reply(client, f"🚀 Bot con '{bot_name}' đã được bật thành công! (PID: {result})", message_object, thread_id, thread_type)
            else:
                _reply(client, f"❌ Cấu hình thành công nhưng bật bot thất bại: {result}", message_object, thread_id, thread_type)

    except ZaloLoginError as e:
        delete_msg(init_msg)
        delete_msg(qr_message_result[0])
        err_msg = str(e)
        if "Het thoi gian cho quet ma QR" in err_msg or "Hết thời gian chờ" in err_msg:
            _reply(client, "⏰ Hết thời gian chờ quét mã QR.", message_object, thread_id, thread_type)
        elif "tu choi" in err_msg or "từ chối" in err_msg:
            _reply(client, "❌ Xác nhận đăng nhập đã bị từ chối trên điện thoại của bạn.", message_object, thread_id, thread_type)
        else:
            _reply(client, f"❌ Lỗi đăng nhập Zalo: {err_msg[:150]}", message_object, thread_id, thread_type)
    except Exception as e:
        delete_msg(init_msg)
        delete_msg(qr_message_result[0])
        _reply(client, f"❌ Đã xảy ra lỗi: {str(e)[:150]}", message_object, thread_id, thread_type)
    finally:
        if os.path.exists(qr_file_path):
            try: os.remove(qr_file_path)
            except: pass

def handle_mybot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id, client):
        _reply(client, "❌ Chỉ admin mới có quyền dùng lệnh này.", message_object, thread_id, thread_type)
        return

    prefix = client.settings.get("prefix", ".")
    args = message.strip().split()
    
    if len(args) < 2:
        help_msg = (
            f"🤖 QUẢN LÝ BOT CON (SUB-BOT)\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👉 {prefix}mybot list : Xem danh sách bot con\n"
            f"👉 {prefix}mybot create <tên_bot> <prefix_mới> : Tạo bot con mới\n"
            f"👉 {prefix}mybot start <tên_bot> : Bật bot con\n"
            f"👉 {prefix}mybot stop <tên_bot> : Tắt bot con"
        )
        _reply(client, help_msg, message_object, thread_id, thread_type)
        return

    sub = args[1].lower()

    # ── LIST BOTS ──
    if sub == "list":
        if not os.path.exists(BOTS_DIR):
            _reply(client, "📭 Chưa có bot con nào được tạo.", message_object, thread_id, thread_type)
            return
        
        bot_folders = [f for f in os.listdir(BOTS_DIR) if os.path.isdir(os.path.join(BOTS_DIR, f))]
        if not bot_folders:
            _reply(client, "📭 Chưa có bot con nào được tạo.", message_object, thread_id, thread_type)
            return
        
        lines = [f"📋 DANH SÁCH BOT CON ({len(bot_folders)})\n━━━━━━━━━━━━━━━━━━"]
        for i, name in enumerate(bot_folders, 1):
            cfg_path = os.path.join(BOTS_DIR, name, "bot_config.json")
            details = "Chưa có cấu hình"
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    pfx = cfg.get("PREFIX", "")
                    created = cfg.get("created_at", "")
                    details = f"Prefix: '{pfx}' | Tạo lúc: {created}"
                except:
                    pass
            
            status = "🟢 Đang chạy" if SubBotManager.is_running(name) else "🔴 Đã tắt"
            lines.append(f"{i}. Bot con: {name} ({status})\n   📄 {details}")
            
        _reply(client, "\n\n".join(lines), message_object, thread_id, thread_type)

    # ── CREATE BOT ──
    elif sub == "create":
        if len(args) < 4:
            _reply(client, f"⚠️ Cú pháp: {prefix}mybot create <tên_bot> <prefix_mới>", message_object, thread_id, thread_type)
            return
        
        bot_name = args[2]
        bot_prefix = args[3]
        
        # Check folder exists
        folder = os.path.join(BOTS_DIR, bot_name)
        if os.path.exists(folder) and os.path.exists(os.path.join(folder, "bot_config.json")):
            _reply(client, f"⚠️ Bot con '{bot_name}' đã tồn tại trong hệ thống.", message_object, thread_id, thread_type)
            return
        
        login_thread = threading.Thread(
            target=login_and_create_subbot,
            args=(client, thread_id, thread_type, message_object, bot_name, bot_prefix, author_id)
        )
        login_thread.daemon = True
        login_thread.start()

    # ── START BOT ──
    elif sub == "start":
        if len(args) < 3:
            _reply(client, f"⚠️ Cú pháp: {prefix}mybot start <tên_bot>", message_object, thread_id, thread_type)
            return
        
        bot_name = args[2]
        folder = os.path.join(BOTS_DIR, bot_name)
        if not os.path.exists(folder):
            _reply(client, f"❌ Bot con '{bot_name}' không tồn tại.", message_object, thread_id, thread_type)
            return
        
        if SubBotManager.is_running(bot_name):
            _reply(client, f"✅ Bot con '{bot_name}' đã đang chạy rồi.", message_object, thread_id, thread_type)
            return
        
        success, result = SubBotManager.start(bot_name, {"folder": folder})
        if success:
            _reply(client, f"🚀 Đã bật bot con '{bot_name}' thành công! (PID: {result})", message_object, thread_id, thread_type)
        else:
            _reply(client, f"❌ Không thể bật bot con: {result}", message_object, thread_id, thread_type)

    # ── STOP BOT ──
    elif sub == "stop":
        if len(args) < 3:
            _reply(client, f"⚠️ Cú pháp: {prefix}mybot stop <tên_bot>", message_object, thread_id, thread_type)
            return
        
        bot_name = args[2]
        if not SubBotManager.is_running(bot_name):
            _reply(client, f"⚠️ Bot con '{bot_name}' hiện tại không chạy.", message_object, thread_id, thread_type)
            return
        
        if SubBotManager.stop(bot_name):
            _reply(client, f"🛑 Đã tắt bot con '{bot_name}' thành công.", message_object, thread_id, thread_type)
        else:
            _reply(client, f"❌ Tắt bot con thất bại.", message_object, thread_id, thread_type)

    else:
        _reply(client, f"❓ Không hiểu lệnh. Gõ {prefix}mybot để xem hướng dẫn.", message_object, thread_id, thread_type)

def LIGHT():
    return {
        "mybot": handle_mybot_command
    }
