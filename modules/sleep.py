# modules/sleep.py
# -*- coding: utf-8 -*-
import time
import threading
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from modules.canvas import *

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Tự động ngủ đông",
    "power": "Admin"
}

_sleep_mode = False
_last_activity = time.time()
_sleep_timeout = 300  # 5 phút mặc định
_check_interval = 10  # Kiểm tra mỗi 10 giây

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def check_activity():
    global _sleep_mode, _last_activity
    while True:
        time.sleep(_check_interval)
        if not _sleep_mode:
            inactive_time = time.time() - _last_activity
            if inactive_time >= _sleep_timeout:
                _sleep_mode = True
                print(f"[SLEEP] 😴 Bot tự ngủ lúc {datetime.now().strftime('%H:%M:%S')} (không hoạt động {inactive_time:.0f}s)")

def update_activity():
    global _last_activity
    _last_activity = time.time()
    if _sleep_mode:
        print(f"[SLEEP] Có hoạt động nhưng bot đang ngủ, cần đánh thức")

def is_sleeping():
    return _sleep_mode

def wake_up():
    global _sleep_mode, _last_activity
    was_sleeping = _sleep_mode
    _sleep_mode = False
    _last_activity = time.time()
    if was_sleeping:
        print(f"[SLEEP] 🔊 Bot được đánh thức lúc {datetime.now().strftime('%H:%M:%S')}")

def handle_sleep(message, message_object, thread_id, thread_type, author_id, client):
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    global _sleep_mode
    _sleep_mode = True
    _reply(client, message_object, thread_id, thread_type, "Đã ngủ")

def handle_wake(message, message_object, thread_id, thread_type, author_id, client):
    if _sleep_mode:
        wake_up()
        _reply(client, message_object, thread_id, thread_type, "Đã thức")
    else:
        _reply(client, message_object, thread_id, thread_type, "🟢 Đang hoạt động")

def handle_status(message, message_object, thread_id, thread_type, author_id, client):
    if _sleep_mode:
        _reply(client, message_object, thread_id, thread_type, "Đang ngủ")
    else:
        remaining = max(0, _sleep_timeout - (time.time() - _last_activity))
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        _reply(client, message_object, thread_id, thread_type, f"🟢 Hoạt động\n⏰ Sẽ ngủ sau: {mins}p {secs}s")

def handle_settime(message, message_object, thread_id, thread_type, author_id, client):
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    global _sleep_timeout
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, "settime <phút>")
        return
    
    try:
        mins = int(parts[1])
        if mins < 1:
            _reply(client, message_object, thread_id, thread_type, "❌ Phải > 0")
            return
        _sleep_timeout = mins * 60
        _reply(client, message_object, thread_id, thread_type, f"✅ {mins} phút")
    except:
        _reply(client, message_object, thread_id, thread_type, "❌ Nhập số")

def LIGHT():
    return {
        "sleep": handle_sleep,
        "wake": handle_wake,
        "sleepstatus": handle_status,
        "settime": handle_settime
    }

# Khởi động thread kiểm tra
_thread = threading.Thread(target=check_activity, daemon=True)
_thread.start()
print(f"[SLEEP] 🟢 Đã khởi động, sẽ ngủ sau {_sleep_timeout//60} phút không hoạt động")