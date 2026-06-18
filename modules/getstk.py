# modules/getstk.py
# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
import requests
import time
from io import BytesIO
from PIL import Image
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Lấy ảnh gốc từ sticker (reply sticker)",
    "power": "USER"
}

CACHE_DIR = "modules/cache/getstk"
os.makedirs(CACHE_DIR, exist_ok=True)

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def handle_getstk(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    if not message_object.quote or not message_object.quote.attach:
        _reply(client, message_object, thread_id, thread_type, f"Reply sticker + {PREFIX}getstk")
        return
    
    _reply(client, message_object, thread_id, thread_type, "⏳ Đang xử lý...")
    
    try:
        attach_data = json.loads(message_object.quote.attach)
        
        sticker_url = attach_data.get('hdUrl') or attach_data.get('href') or attach_data.get('sticker')
        if not sticker_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy sticker")
            return
        
        sticker_url = urllib.parse.unquote(sticker_url.replace("\\/", "/"))
        
        r = requests.get(sticker_url, timeout=30)
        
        ext = 'png' if 'png' in r.headers.get('Content-Type', '') else 'jpg'
        path = os.path.join(CACHE_DIR, f"stk_{int(time.time())}.{ext}")
        
        with open(path, 'wb') as f:
            f.write(r.content)
        
        client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type)
        os.remove(path)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:80]}")

def LIGHT():
    return {"getstk": handle_getstk}