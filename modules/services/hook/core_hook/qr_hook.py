# modules/services/hook/core_hook/qr_hook.py
import time
import threading

shutdown_event = threading.Event()

def check():
    from modules.engine.data.data import jsonLoader
    data = jsonLoader("asset/config/login.json", {})
    return bool(data.get("data"))

def qr():
    print("[QR] Đang chờ quét mã QR...")
    time.sleep(2)
    return None

class ThreadType:
    USER = "user"
    GROUP = "group"

class Message:
    def __init__(self, text=None):
        self.text = text or ""

class Mention:
    def __init__(self, uid, offset=0, length=0):
        self.uid = uid
        self.offset = offset
        self.length = length

logger = type('Logger', (), {
    'debug': lambda *args, **kwargs: print(f"[DEBUG] {args[0] if args else ''}"),
    'errorMeta': lambda *args, **kwargs: print(f"[ERROR] {args[0] if args else ''}"),
    'warning': lambda *args, **kwargs: print(f"[WARNING] {args[0] if args else ''}"),
    'info': lambda *args, **kwargs: print(f"[INFO] {args[0] if args else ''}"),
    'base': lambda *args, **kwargs: print(f"[BASE] {args[0] if args else ''}"),
    'start': lambda *args, **kwargs: print(f"[START] {args[0] if args else ''}"),
})()
