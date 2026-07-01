# modules/avatar.py
# -*- coding: utf-8 -*-
import os
import requests
import time
import json
from datetime import datetime
from PIL import Image
from io import BytesIO
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Lấy avatar người dùng",
    "power": "Admin"
}

CACHE_PATH = "modules/cache/avatar"
os.makedirs(CACHE_PATH, exist_ok=True)

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def get_avatar_url(client, uid):
    """Lấy avatar URL của user"""
    try:
        info = client.fetchUserInfo(uid)
        profile = info.changed_profiles.get(str(uid), {})
        return profile.get('avatar', '')
    except:
        return None

def download_avatar(url, uid):
    """Tải avatar về máy"""
    try:
        path = os.path.join(CACHE_PATH, f"avatar_{uid}_{int(time.time())}.jpg")
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        with open(path, 'wb') as f:
            f.write(r.content)
        return path
    except:
        return None

def handle_getavt(message, message_object, thread_id, thread_type, author_id, client):
    """Lấy avatar người dùng"""
    from asset.config import PREFIX
    
    uid = None
    
    # Check reply
    if hasattr(message_object, 'replyId') and message_object.replyId:
        try:
            replied = client.fetchMessage(thread_id, message_object.replyId)
            if replied:
                uid = replied.authorId
        except:
            pass
    
    # Check mention
    if not uid and message_object.mentions:
        uid = message_object.mentions[0]['uid']
    
    # Check tin nhắn chứa uid
    if not uid:
        parts = message.split()
        if len(parts) > 1 and parts[1].strip().isdigit():
            uid = parts[1].strip()
    
    # Nếu vẫn không có, lấy avatar người gửi
    if not uid:
        uid = author_id
    
    # Lấy avatar
    avatar_url = get_avatar_url(client, uid)
    if not avatar_url:
        _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được avatar")
        return
    
    # Tải và gửi
    avatar_path = download_avatar(avatar_url, uid)
    if avatar_path:
        client.sendLocalImage(avatar_path, thread_id=thread_id, thread_type=thread_type)
        os.remove(avatar_path)
    else:
        _reply(client, message_object, thread_id, thread_type, "❌ Lỗi tải avatar")

def handle_setavt(message, message_object, thread_id, thread_type, author_id, client):
    """Hướng dẫn đặt avatar (không thể tự đặt qua API)"""
    from asset.config import PREFIX
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    _reply(client, message_object, thread_id, thread_type, 
           f"📝 ĐỔI AVATAR BOT\n\n"
           f"Zalo không hỗ trợ đổi avatar qua API.\n\n"
           f"Cách thủ công:\n"
           f"1. Vào profile bot trên Zalo\n"
           f"2. Bấm vào avatar\n"
           f"3. Chọn ảnh mới\n\n"
           f"Hoặc dùng lệnh {PREFIX}getavt để lấy avatar người khác")

def Kryzis():
    return {
        "getavt": handle_getavt,
        "setavt": handle_setavt
    }