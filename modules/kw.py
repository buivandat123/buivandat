# modules/kw.py
# -*- coding: utf-8 -*-
import os
import json
import random
import time
import urllib.parse
import requests
import re
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "3.0.0",
    "credits": "Kryzis",
    "description": "Tự động trả lời theo từ khóa (chính xác 100%)",
    "power": "ADMIN"
}

KW_FILE = "modules/cache/keywords.json"
MEDIA_DIR = "modules/cache/kw_media"
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(KW_FILE), exist_ok=True)

_last_trigger = {}
_spam_cooldown = 2

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
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        with open(path, 'wb') as f:
            f.write(r.content)
        return path
    except:
        return None

def upload_to_catbox(file_path):
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://catbox.moe/user/api.php', files={'fileToUpload': f}, data={'reqtype': 'fileupload'}, timeout=30)
            if r.status_code == 200 and r.text.startswith('https://'):
                return r.text.strip()
    except:
        pass
    return None

def handle_kw_add(message, message_object, thread_id, thread_type, author_id, client, prefix):
    raw = message[len(prefix + "kw add"):].strip()
    
    if hasattr(message_object, 'quote') and message_object.quote and message_object.quote.attach:
        try:
            attach_data = json.loads(message_object.quote.attach)
            media_url = attach_data.get('href')
            
            if not media_url and 'params' in attach_data:
                try:
                    params = json.loads(attach_data['params'])
                    media_url = params.get('hd') or params.get('url')
                except:
                    pass
            
            if media_url and raw:
                media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
                keyword = raw.lower()
                
                if attach_data.get('msgBubbleLayoutType') == 3 or 'webp' in str(attach_data):
                    data = load_data()
                    if keyword not in data:
                        data[keyword] = []
                    data[keyword].append({
                        "type": "sticker",
                        "value": media_url,
                        "author": author_id,
                        "time": datetime.now().strftime("%d/%m/%Y %H:%M")
                    })
                    save_data(data)
                    _reply(client, message_object, thread_id, thread_type, f"✅ Sticker: {keyword}")
                    return
                else:
                    def process():
                        path = download_media(media_url, 'jpg')
                        if path:
                            catbox_url = upload_to_catbox(path)
                            os.remove(path)
                            if catbox_url:
                                data = load_data()
                                if keyword not in data:
                                    data[keyword] = []
                                data[keyword].append({
                                    "type": "photo",
                                    "value": catbox_url,
                                    "author": author_id,
                                    "time": datetime.now().strftime("%d/%m/%Y %H:%M")
                                })
                                save_data(data)
                                _reply(client, message_object, thread_id, thread_type, f"✅ Ảnh: {keyword}")
                            else:
                                _reply(client, message_object, thread_id, thread_type, "❌ Upload ảnh thất bại")
                    import threading
                    threading.Thread(target=process, daemon=True).start()
                    _reply(client, message_object, thread_id, thread_type, f"⏳ Đang thêm ảnh: {keyword}")
                    return
        except:
            pass
    
    if not raw:
        _reply(client, message_object, thread_id, thread_type, 
               f"CÁCH DÙNG:\n{prefix}kw add từ khóa | nội dung\nReply + {prefix}kw add từ khóa")
        return
    
    if '|' not in raw:
        _reply(client, message_object, thread_id, thread_type, f"Dùng dấu | để phân cách\nVD: {prefix}kw add jz | jz má")
        return
    
    parts = raw.split('|', 1)
    keyword = parts[0].strip().lower()
    content = parts[1].strip()
    
    if not keyword or not content:
        return
    
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

def handle_kw_remove(message, message_object, thread_id, thread_type, author_id, client, prefix):
    content = message[len(prefix + "kw remove"):].strip()
    if not content:
        _reply(client, message_object, thread_id, thread_type, f"{prefix}kw remove <từ khóa>")
        return
    
    keyword = content.strip().lower()
    data = load_data()
    
    if keyword not in data:
        _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {keyword}")
        return
    
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
        _reply(client, message_object, thread_id, thread_type, "📭 Chưa có từ khóa")
        return
    
    lines = ["📋 DANH SÁCH TỪ KHÓA", ""]
    for kw, replies in data.items():
        lines.append(f"🔑 {kw} ({len(replies)} đáp ứng)")
        for i, r in enumerate(replies, 1):
            if r['type'] == 'text':
                txt = r['value'][:35]
                lines.append(f"   {i}. [Text] {txt}")
            elif r['type'] == 'photo':
                lines.append(f"   {i}. [🖼️ Ảnh]")
            elif r['type'] == 'sticker':
                lines.append(f"   {i}. [🎨 Sticker]")
        lines.append("")
    _reply(client, message_object, thread_id, thread_type, "\n".join(lines))

def handle_kw_clear(message, message_object, thread_id, thread_type, author_id, client, prefix):
    for f in os.listdir(MEDIA_DIR):
        try:
            os.remove(os.path.join(MEDIA_DIR, f))
        except:
            pass
    save_data({})
    _reply(client, message_object, thread_id, thread_type, "🗑️ Đã xóa toàn bộ")

def handle_kw_command(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, 
               f"{PREFIX}kw add từ khóa | nội dung\nReply + {PREFIX}kw add từ khóa\n{PREFIX}kw remove từ khóa\n{PREFIX}kw list\n{PREFIX}kw clear")
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
            r = requests.get(value, timeout=10)
            temp = os.path.join(MEDIA_DIR, f"temp_{int(time.time())}.jpg")
            with open(temp, 'wb') as f:
                f.write(r.content)
            client.sendLocalImage(temp, thread_id=thread_id, thread_type=thread_type)
            os.remove(temp)
        elif media_type == 'sticker':
            client.sendCustomSticker(staticImgUrl=value, animationImgUrl=value,
                                    thread_id=thread_id, thread_type=thread_type,
                                    width=512, height=512)
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
    
    msg_lower = message_text.lower().strip()
    
    for keyword, replies in data.items():
        # So sánh chính xác toàn bộ tin nhắn với từ khóa
        if msg_lower == keyword.lower():
            entry = random.choice(replies)
            send_media(client, entry['type'], entry['value'], thread_id, thread_type)
            return

def on_message(message_text, message_object, thread_id, thread_type, client):
    check_keyword(message_text, client, thread_id, thread_type)

def LIGHT():
    return {"kw": handle_kw_command}