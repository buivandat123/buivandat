# modules/kryzisbot.py
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import signal
import time
import json
import threading
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Quản lý bot con chạy cùng bot mẹ",
    "power": "Admin"
}

BOTS_DIR = "/sdcard/download/kryzis/modules/bots/nguyen"
os.makedirs(BOTS_DIR, exist_ok=True)

CACHE_FILE = "modules/cache/kryzis_bots.json"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def load_bots():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_bots(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_bot_files():
    """Lấy danh sách file .py trong thư mục filebot"""
    bots = []
    if os.path.exists(BOTS_DIR):
        for f in os.listdir(BOTS_DIR):
            if f.endswith('.py') and f != '__init__.py':
                bots.append(f)
    return bots

def run_bot(bot_file, bot_id):
    """Chạy file bot con"""
    bot_path = os.path.join(BOTS_DIR, bot_file)
    pid_file = os.path.join(BOTS_DIR, f"{bot_id}.pid")
    
    try:
        proc = subprocess.Popen(
            [sys.executable, bot_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        with open(pid_file, 'w') as f:
            f.write(str(proc.pid))
        return True, proc.pid
    except Exception as e:
        return False, str(e)

def stop_bot(bot_id):
    """Dừng bot con"""
    pid_file = os.path.join(BOTS_DIR, f"{bot_id}.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read())
            os.kill(pid, signal.SIGTERM)
            os.remove(pid_file)
            return True
        except:
            pass
    return False

def handle_kryzisbot(message, message_object, thread_id, thread_type, author_id, client):
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, 
               "kryzisbot on <số> - Bật bot\nkryzisbot off <số> - Tắt bot\nkryzisbot list - Xem danh sách")
        return
    
    cmd = parts[1].lower()
    
    # Lấy danh sách file bot
    bot_files = get_bot_files()
    if not bot_files:
        _reply(client, message_object, thread_id, thread_type, "❌ Không có file bot trong thư mục filebot")
        return
    
    if cmd == "list":
        lines = [f"📋 DANH SÁCH BOT ({len(bot_files)})"]
        for i, f in enumerate(bot_files, 1):
            lines.append(f"{i}. {f}")
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines))
        return
    
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type, "kryzisbot on <số>\nkryzisbot off <số>")
        return
    
    try:
        bot_num = int(parts[2]) - 1
        if bot_num < 0 or bot_num >= len(bot_files):
            _reply(client, message_object, thread_id, thread_type, f"❌ Số từ 1 đến {len(bot_files)}")
            return
    except:
        _reply(client, message_object, thread_id, thread_type, "❌ Phải nhập số")
        return
    
    bot_file = bot_files[bot_num]
    bot_id = bot_file.replace('.py', '')
    
    if cmd == "on":
        # Kiểm tra đã chạy chưa
        pid_file = os.path.join(BOTS_DIR, f"{bot_id}.pid")
        if os.path.exists(pid_file):
            _reply(client, message_object, thread_id, thread_type, f"✅ Bot {bot_id} đang chạy")
            return
        
        success, result = run_bot(bot_file, bot_id)
        if success:
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã bật: {bot_id} (PID: {result})")
        else:
            _reply(client, message_object, thread_id, thread_type, f"❌ Lỗi: {result}")
    
    elif cmd == "off":
        if stop_bot(bot_id):
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã tắt: {bot_id}")
        else:
            _reply(client, message_object, thread_id, thread_type, f"❌ Bot {bot_id} không chạy")
    
    else:
        _reply(client, message_object, thread_id, thread_type, "kryzisbot on/off/list")

def LIGHT():
    return {"kryzisbot": handle_kryzisbot}