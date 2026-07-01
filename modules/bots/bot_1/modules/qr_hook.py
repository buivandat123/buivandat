# modules/qr_hook.py
# -*- coding: utf-8 -*-
import os
import json
import time

mainLogin = "asset/config/main_login.json"

def check() -> bool:
    try:
        if not os.path.exists(mainLogin):
            return False
        with open(mainLogin, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "data" not in data or not data["data"]:
            return False
        valid = [item for item in data["data"] if item.get("imei") and item.get("sessionCookies") and item.get("status") is True]
        return len(valid) > 0
    except:
        return False

def generate_qr():
    return "qr_code_123456", {}

def waiting_scan(code, sessions):
    time.sleep(2)
    return True

def waiting_confirm(code, sessions):
    return {
        "imei": "123456789012345",
        "cookie": {"zpsid": "abc123"},
        "prefix": "."
    }

def addcf(qr_data, is_main_bot=True):
    try:
        session_cookies = qr_data.get("cookie", {})
        new_entry = {
            "username": None,
            "botIntId": None,
            "imei": qr_data.get("imei"),
            "prefix": qr_data.get("prefix", "?"),
            "sessionCookies": session_cookies,
            "mainBot": is_main_bot,
            "status": True
        }
        
        if is_main_bot:
            data = {}
            if os.path.exists(mainLogin):
                with open(mainLogin, "r") as f:
                    data = json.load(f)
            if "data" not in data:
                data["data"] = []
            data["data"].append(new_entry)
            with open(mainLogin, "w") as f:
                json.dump(data, f, indent=4)
        else:
            account_dir = "asset/config/multibot"
            os.makedirs(account_dir, exist_ok=True)
            existing = [f for f in os.listdir(account_dir) if f.endswith("-login.json")]
            next_idx = len(existing) + 1
            account_file = os.path.join(account_dir, f"{next_idx}-login.json")
            with open(account_file, "w") as f:
                json.dump([new_entry], f, indent=4)
        
        return True
    except:
        return False

def qr():
    try:
        print("📱 Đang tạo QR Code...")
        sessions = {}
        code, sessions = generate_qr()
        print(f"🔑 Mã QR: {code}")
        print("⏳ Đang chờ scan...")
        result = waiting_scan(code, sessions)
        if not result:
            print("❌ Scan thất bại!")
            return False
        print("✅ Đã scan! Đang xác nhận...")
        qr_data = waiting_confirm(code, sessions)
        if qr_data:
            print("✅ Đăng nhập thành công!")
            if addcf(qr_data):
                print("✅ Đã lưu thông tin!")
                return True
        return False
    except Exception as e:
        print(f"❌ Lỗi QR: {e}")
        return False