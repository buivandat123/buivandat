# modules/get_commands.py
# -*- coding: utf-8 -*-
import os
import shutil
from zlapi.models import Message

des = {
    'version': "1.0.0",
    'credits': "Kryzis",
    'description': "Lấy tất cả lệnh từ bot zBug",
    'power': "Admin"
}

def handle_getcmd(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Kiểm tra admin
        if str(author_id) != "696983558841863982":
            client.replyMessage(Message(text="❌ Chỉ admin mới dùng!"), message_object, thread_id, thread_type, ttl=60000)
            return
        
        client.replyMessage(Message(text="⏳ Đang lấy lệnh từ zBug..."), message_object, thread_id, thread_type, ttl=30000)
        
        # Backup lệnh cũ
        backup_dir = "/sdcard/download/kryzis/modules_backup"
        if not os.path.exists(backup_dir):
            shutil.copytree("/sdcard/download/kryzis/modules", backup_dir)
            client.replyMessage(Message(text="✅ Đã backup lệnh cũ"), message_object, thread_id, thread_type, ttl=10000)
        
        # Copy lệnh mới từ zBug
        src = "/sdcard/download/Zalo/zBug/modules"
        dst = "/sdcard/download/kryzis/modules"
        
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        
        client.replyMessage(Message(text="✅ Đã lấy toàn bộ lệnh từ zBug! Khởi động lại bot để dùng."), message_object, thread_id, thread_type, ttl=60000)
        
    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type, ttl=60000)

def LIGHT():
    return {"getcmd": handle_getcmd}