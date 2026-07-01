# modules/pin.py
# -*- coding: utf-8 -*-
import os
import json
import requests
import random
import time
from io import BytesIO
from PIL import Image
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tìm kiếm ảnh trên Pinterest",
    "power": "USER"
}

CACHE_DIR = "modules/cache/pin"
os.makedirs(CACHE_DIR, exist_ok=True)

API_URL = "https://nqduan.id.vn/api/pinterest"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def handle_pin(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, 
               f"{PREFIX}pin ")
        return
    
    query = " ".join(parts[1:])
    limit = 10
    
    _reply(client, message_object, thread_id, thread_type, f"🔍 Đang tìm: {query}")
    
    try:
        r = requests.get(API_URL, params={"query": query, "limit": limit}, timeout=30)
        
        if r.status_code != 200:
            _reply(client, message_object, thread_id, thread_type, "❌ API lỗi")
            return
        
        data = r.json()
        
        if not data.get('success') or not data.get('images'):
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy ảnh")
            return
        
        images = data['images']
        img_url = random.choice(images)
        
        img_r = requests.get(img_url, timeout=30)
        temp_path = os.path.join(CACHE_DIR, f"pin_{int(time.time())}.jpg")
        with open(temp_path, 'wb') as f:
            f.write(img_r.content)
        
        client.sendLocalImage(temp_path, thread_id=thread_id, thread_type=thread_type,
                              message=Message(text=f"🖼️ {query}"))
        os.remove(temp_path)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def handle_pinall(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, f"{PREFIX}pinall <từ khóa>")
        return
    
    query = " ".join(parts[1:])
    limit = 5
    
    _reply(client, message_object, thread_id, thread_type, f"🔍 Đang tìm: {query}")
    
    try:
        r = requests.get(API_URL, params={"query": query, "limit": limit}, timeout=30)
        
        if r.status_code != 200:
            _reply(client, message_object, thread_id, thread_type, "❌ API lỗi")
            return
        
        data = r.json()
        
        if not data.get('success') or not data.get('images'):
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy ảnh")
            return
        
        images = data['images']
        
        for i, img_url in enumerate(images[:5]):
            try:
                img_r = requests.get(img_url, timeout=30)
                temp_path = os.path.join(CACHE_DIR, f"pin_{i}_{int(time.time())}.jpg")
                with open(temp_path, 'wb') as f:
                    f.write(img_r.content)
                
                client.sendLocalImage(temp_path, thread_id=thread_id, thread_type=thread_type)
                os.remove(temp_path)
            except:
                continue
        
        _reply(client, message_object, thread_id, thread_type, f"✅ Đã gửi {len(images)} ảnh: {query}")
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def Kryzis():
    return {
        "pin": handle_pin,
        "pinall": handle_pinall
    }