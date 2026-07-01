# modules/filemanager.py
# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Quản lý file",
    "power": "ADMIN"
}

BASE_PATH = "/storage/emulated/0/Download/kryzis"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def normalize_path(path):
    if not path:
        return None
    if path.startswith('<') and path.endswith('>'):
        path = path[1:-1]
    if path.startswith('/'):
        return path
    if path.startswith('storage/'):
        return '/' + path
    if path.startswith('sdcard/'):
        return '/' + path
    return os.path.join(BASE_PATH, path)

def upload_file(client, file_path, thread_id, thread_type):
    """Upload file lên server và trả về link (dùng uploadAttachment)"""
    try:
        up = client.uploadAttachment(file_path, thread_id, thread_type)
        if up and 'fileUrl' in up:
            return up['fileUrl']
        return None
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def handle_filemanager(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    parts = message.split(maxsplit=2)
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type,
               f"CÁCH DÙNG:\n"
               f"{PREFIX}filemanager --edit <đường dẫn> | <nội dung>\n"
               f"{PREFIX}filemanager --read <đường dẫn>\n"
               f"{PREFIX}filemanager --create <đường dẫn> | <nội dung>\n"
               f"{PREFIX}filemanager --delete <đường dẫn>\n"
               f"{PREFIX}filemanager --list <đường dẫn>\n"
               f"{PREFIX}filemanager --upload <đường dẫn>")
        return
    
    cmd = parts[1].lower()
    
    # --list
    if cmd == '--list':
        path = parts[2].strip() if len(parts) > 2 else ""
        full_path = normalize_path(path) if path else BASE_PATH
        
        try:
            if not os.path.exists(full_path):
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tồn tại")
                return
            
            items = os.listdir(full_path)
            lines = [f"📁 {full_path} ({len(items)} items)"]
            for item in sorted(items)[:50]:
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    lines.append(f"📂 {item}")
                else:
                    size = os.path.getsize(item_path)
                    lines.append(f"📄 {item} ({size} bytes)")
            if len(items) > 50:
                lines.append(f"... và {len(items)-50} items khác")
            _reply(client, message_object, thread_id, thread_type, "\n".join(lines))
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {e}")
        return
    
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type, f"Thiếu đường dẫn")
        return
    
    content_part = parts[2].strip()
    
    # --read
    if cmd == '--read':
        path = content_part
        full_path = normalize_path(path)
        try:
            if not os.path.exists(full_path):
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {full_path}")
                return
            
            with open(full_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            if len(file_content) > 1500:
                for i in range(0, len(file_content), 1500):
                    _reply(client, message_object, thread_id, thread_type, file_content[i:i+1500])
            else:
                _reply(client, message_object, thread_id, thread_type, f"📄 {full_path}\n\n{file_content}")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {e}")
        return
    
    # --delete
    if cmd == '--delete':
        path = content_part
        full_path = normalize_path(path)
        try:
            if not os.path.exists(full_path):
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {full_path}")
                return
            os.remove(full_path)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã xóa: {full_path}")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {e}")
        return
    
    # --upload (upload lấy link)
    if cmd == '--upload':
        path = content_part
        full_path = normalize_path(path)
        try:
            if not os.path.exists(full_path):
                _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {full_path}")
                return
            
            file_name = os.path.basename(full_path)
            file_size = os.path.getsize(full_path)
            
            _reply(client, message_object, thread_id, thread_type, f"⏳ Đang upload: {file_name} ({file_size} bytes)")
            
            url = upload_file(client, full_path, thread_id, thread_type)
            if url:
                _reply(client, message_object, thread_id, thread_type, f"✅ Đã upload: {file_name}\n🔗 {url}")
                
                # Thử gửi file qua link nếu có thể
                try:
                    if file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        client.sendLocalImage(url, thread_id=thread_id, thread_type=thread_type)
                    elif file_name.endswith('.mp3'):
                        client.sendLocalVoice(url, thread_id=thread_id, thread_type=thread_type)
                    elif file_name.endswith('.mp4'):
                        client.sendLocalVideo(url, thread_id=thread_id, thread_type=thread_type)
                except:
                    pass
            else:
                _reply(client, message_object, thread_id, thread_type, f"❌ Upload thất bại")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {e}")
        return
    
    # --edit và --create
    if '|' not in content_part:
        _reply(client, message_object, thread_id, thread_type, f"Dùng dấu | để phân cách đường dẫn và nội dung")
        return
    
    path, content = content_part.split('|', 1)
    path = path.strip()
    content = content.strip()
    full_path = normalize_path(path)
    
    if cmd == '--edit':
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã lưu: {full_path}")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {e}")
    
    elif cmd == '--create':
        try:
            if os.path.exists(full_path):
                _reply(client, message_object, thread_id, thread_type, f"⚠️ File đã tồn tại")
                return
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã tạo: {full_path}")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {e}")
    
    else:
        _reply(client, message_object, thread_id, thread_type, f"❌ Lệnh không hợp lệ: {cmd}")

def Kryzis():
    return {"filemanager": handle_filemanager}