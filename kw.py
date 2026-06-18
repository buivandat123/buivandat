# modules/kw.py
# -*- coding: utf-8 -*-
import os
import json
import random
import time
import urllib.parse
import requests
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "3.0.0",
    "credits": "Kryzis",
    "description": "Tự động trả lời theo từ khóa",
    "power": "ADMIN"
}

KW_FILE = "modules/cache/keywords.json"
MEDIA_DIR = "modules/cache/kw_media"
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(KW_FILE), exist_ok=True)

_last_trigger = {}
_spam_cooldown = 3

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def load_data():
    if os.path.exists(KW_FILE):
        try:
            with open(KW_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(KW_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def download_media(url, ext):
    try:
        filename = f"{int(time.time())}_{random.randint(1000,9999)}.{ext}"
        path = os.path.join(MEDIA_DIR, filename)
        r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        with open(path, 'wb') as f:
            f.write(r.content)
        return path
    except:
        return None

def handle_kw_add(message, message_object, thread_id, thread_type, author_id, client, prefix):
    # Lấy phần sau lệnh kw add
    raw = message[len(prefix + "kw add"):].strip()
    
    # KIỂM TRA REPLY TRƯỚC HẾT
    if hasattr(message_object, 'replyId') and message_object.replyId:
        try:
            replied = client.fetchMessage(thread_id, message_object.replyId)
            
            if replied:
                content = replied.content
                
                if isinstance(content, dict):
                    # Lấy URL sticker
                    sticker_url = content.get('sticker') or content.get('stickerId')
                    # Lấy URL ảnh
                    photo_url = content.get('photo')
                    # Lấy URL video
                    video_url = content.get('video')
                    
                    # Ưu tiên sticker
                    if sticker_url:
                        if not raw:
                            _reply(client, message_object, thread_id, thread_type, f"Thiếu từ khóa\nVD: {prefix}kw add ten")
                            return
                        
                        keyword = raw.lower()
                        data = load_data()
                        if keyword not in data:
                            data[keyword] = []
                        data[keyword].append({
                            "type": "sticker",
                            "value": sticker_url,
                            "author": author_id,
                            "time": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        save_data(data)
                        _reply(client, message_object, thread_id, thread_type, f"✅ Sticker: {keyword}")
                        return
                    
                    # Nếu không có sticker, kiểm tra ảnh
                    if photo_url:
                        if not raw:
                            _reply(client, message_object, thread_id, thread_type, f"Thiếu từ khóa\nVD: {prefix}kw add ten")
                            return
                        
                        keyword = raw.lower()
                        path = download_media(photo_url, 'jpg')
                        if path:
                            data = load_data()
                            if keyword not in data:
                                data[keyword] = []
                            data[keyword].append({
                                "type": "photo",
                                "value": path,
                                "author": author_id,
                                "time": datetime.now().strftime("%d/%m/%Y %H:%M")
                            })
                            save_data(data)
                            _reply(client, message_object, thread_id, thread_type, f"✅ Ảnh: {keyword}")
                            return
                    
                    # Nếu có video
                    if video_url:
                        if not raw:
                            _reply(client, message_object, thread_id, thread_type, f"Thiếu từ khóa\nVD: {prefix}kw add ten")
                            return
                        
                        keyword = raw.lower()
                        path = download_media(video_url, 'mp4')
                        if path:
                            data = load_data()
                            if keyword not in data:
                                data[keyword] = []
                            data[keyword].append({
                                "type": "video",
                                "value": path,
                                "author": author_id,
                                "time": datetime.now().strftime("%d/%m/%Y %H:%M")
                            })
                            save_data(data)
                            _reply(client, message_object, thread_id, thread_type, f"✅ Video: {keyword}")
                            return
                            
        except Exception as e:
            print(f"Lỗi xử lý reply: {e}")
    
    # XỬ LÝ TEXT (không có reply hoặc không tìm thấy media)
    # Nếu không có từ khóa
    if not raw:
        _reply(client, message_object, thread_id, thread_type, 
               f"CÁCH DÙNG:\n\n"
               f"📝 Text: {prefix}kw add từ khóa | nội dung\n"
               f"🖼️ Ảnh/Sticker: Reply + {prefix}kw add từ khóa\n"
               f"📌 VD: {prefix}kw add jz | jz má")
        return
    
    # Nếu có dấu | thì xử lý text
    if '|' in raw:
        parts = raw.split('|', 1)
        keyword = parts[0].strip().lower()
        content = parts[1].strip()
        
        if keyword and content:
            data = load_data()
            if keyword not in data:
                data[keyword] = []
            data[keyword].append({
                "type": "text",
                "value": content,
                "author": author_id,
                "time": datetime.now().strftime("%d/%m/%Y %H:%M")
            })
            save_data(data)
            _reply(client, message_object, thread_id, thread_type, f"✅ Text: {keyword}")
            return
    
    # Nếu không có dấu |, báo lỗi
    _reply(client, message_object, thread_id, thread_type, f"Dùng dấu | để phân cách\nVD: {prefix}kw add jz | jz má")

def handle_kw_remove(message, message_object, thread_id, thread_type, author_id, client, prefix):
    content = message[len(prefix + "kw remove"):].strip()
    if not content:
        _reply(client, message_object, thread_id, thread_type, f"{prefix}kw remove <từ khóa> [số]")
        return
    
    parts = content.split()
    keyword = parts[0].lower()
    data = load_data()
    
    if keyword not in data:
        _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {keyword}")
        return
    
    if len(parts) > 1 and parts[1].isdigit():
        idx = int(parts[1]) - 1
        if 0 <= idx < len(data[keyword]):
            entry = data[keyword][idx]
            if entry.get('type') in ['photo', 'video'] and os.path.exists(entry.get('value', '')):
                try:
                    os.remove(entry['value'])
                except:
                    pass
            data[keyword].pop(idx)
            if not data[keyword]:
                del data[keyword]
            save_data(data)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã xóa mục {idx+1} của: {keyword}")
        else:
            _reply(client, message_object, thread_id, thread_type, f"❌ Số không hợp lệ (1-{len(data[keyword])})")
    else:
        for entry in data[keyword]:
            if entry.get('type') in ['photo', 'video'] and os.path.exists(entry.get('value', '')):
                try:
                    os.remove(entry['value'])
                except:
                    pass
        del data[keyword]
        save_data(data)
        _reply(client, message_object, thread_id, thread_type, f"✅ Đã xóa: {keyword}")

def handle_kw_list(message, message_object, thread_id, thread_type, author_id, client, prefix):
    data = load_data()
    if not data:
        _reply(client, message_object, thread_id, thread_type, "📭 Chưa có từ khóa nào")
        return
    
    lines = ["📋 DANH SÁCH TỪ KHÓA", ""]
    for kw, replies in data.items():
        lines.append(f"🔑 {kw} ({len(replies)} đáp ứng)")
        for i, r in enumerate(replies, 1):
            if r['type'] == 'text':
                txt = r['value'][:40] + ('...' if len(r['value']) > 40 else '')
                lines.append(f"   {i}. [Text] {txt}")
            elif r['type'] == 'photo':
                lines.append(f"   {i}. [🖼️ Ảnh]")
            elif r['type'] == 'sticker':
                lines.append(f"   {i}. [🎨 Sticker]")
            elif r['type'] == 'video':
                lines.append(f"   {i}. [🎬 Video]")
        lines.append("")
    
    _reply(client, message_object, thread_id, thread_type, "\n".join(lines))

def handle_kw_clear(message, message_object, thread_id, thread_type, author_id, client, prefix):
    for f in os.listdir(MEDIA_DIR):
        try:
            os.remove(os.path.join(MEDIA_DIR, f))
        except:
            pass
    save_data({})
    _reply(client, message_object, thread_id, thread_type, "🗑️ Đã xóa toàn bộ từ khóa")

def handle_kw_command(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, 
               f"📖 KW\n\n{PREFIX}kw add từ khóa | nội dung\nReply + {PREFIX}kw add từ khóa\n{PREFIX}kw remove từ khóa\n{PREFIX}kw list\n{PREFIX}kw clear")
        return
    
    cmd = parts[1].lower()
    
    if cmd == "add":
        handle_kw_add(message, message_object, thread_id, thread_type, author_id, client, PREFIX)
    elif cmd in ["remove", "rm"]:
        handle_kw_remove(message, message_object, thread_id, thread_type, author_id, client, PREFIX)
    elif cmd == "list":
        handle_kw_list(message, message_object, thread_id, thread_type, author_id, client, PREFIX)
    elif cmd == "clear":
        handle_kw_clear(message, message_object, thread_id, thread_type, author_id, client, PREFIX)
    else:
        _reply(client, message_object, thread_id, thread_type, "kw add|remove|list|clear")

def send_media(client, media_type, value, thread_id, thread_type):
    try:
        if media_type == 'text':
            client.send(Message(text=value), thread_id, thread_type, ttl=60000)
        elif media_type == 'photo':
            if os.path.exists(value):
                client.sendLocalImage(value, thread_id=thread_id, thread_type=thread_type)
        elif media_type == 'sticker':
            client.sendSticker(value, thread_id=thread_id, thread_type=thread_type)
        elif media_type == 'video':
            if os.path.exists(value):
                client.sendLocalVideo(value, thread_id=thread_id, thread_type=thread_type)
    except:
        pass

def check_keyword(message_text, client, thread_id, thread_type):
    global _last_trigger
    
    if not message_text:
        return
    
    data = load_data()
    if not data:
        return
    
    now = time.time()
    if thread_id in _last_trigger:
        if now - _last_trigger[thread_id] < _spam_cooldown:
            return
    _last_trigger[thread_id] = now
    
    msg_lower = message_text.lower()
    for keyword, replies in data.items():
        if keyword in msg_lower:
            entry = random.choice(replies)
            send_media(client, entry['type'], entry['value'], thread_id, thread_type)
            return

def on_message(message_text, message_object, thread_id, thread_type, client):
    check_keyword(message_text, client, thread_id, thread_type)

def LIGHT():
    return {"kw": handle_kw_command}