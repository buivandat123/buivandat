# modules/anhtho.py
# -*- coding: utf-8 -*-
import os
import requests
import time
from io import BytesIO
from PIL import Image
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Ghép avatar lên ảnh thờ",
    "power": "Thành viên"
}

CACHE_PATH = "modules/cache/anhtho"
TEMPLATE_PATH = os.path.join(CACHE_PATH, "template.png")
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

def download_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        pass
    return None

def get_avatar_url(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        profile = info.changed_profiles.get(str(uid), {})
        return profile.get('avatar')
    except:
        return None

def resize_fill_crop(img, target_w, target_h):
    """Cắt ảnh vừa khung chữ nhật, giữ tỷ lệ"""
    w, h = img.size
    ratio_w = target_w / w
    ratio_h = target_h / h
    ratio = max(ratio_w, ratio_h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def get_template():
    """Lấy ảnh nền"""
    # Thử đọc file local
    if os.path.exists(TEMPLATE_PATH):
        return Image.open(TEMPLATE_PATH).convert("RGBA")
    
    # URL ảnh mẫu
    template_url = "https://cdn.phototourl.com/free/2026-06-09-95335e41-ad38-400f-ae4e-db4f4ee16b41.png"
    img = download_image(template_url)
    if img:
        img.save(TEMPLATE_PATH)
        return img
    return None

def handle_anhtho(message, message_object, thread_id, thread_type, author_id, client):
    # Lấy UID
    target_uid = None
    if hasattr(message_object, 'replyId') and message_object.replyId:
        try:
            replied = client.fetchMessage(thread_id, message_object.replyId)
            if replied:
                target_uid = replied.authorId
        except:
            pass
    if not target_uid and message_object.mentions:
        target_uid = message_object.mentions[0]['uid']
    if not target_uid:
        target_uid = author_id
    
    _reply(client, message_object, thread_id, thread_type, "⏳ Đang xử lý...")
    
    try:
        # Lấy avatar
        avatar_url = get_avatar_url(client, target_uid)
        if not avatar_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được avatar")
            return
        
        avatar = download_image(avatar_url)
        if not avatar:
            _reply(client, message_object, thread_id, thread_type, "❌ Không tải được avatar")
            return
        
        # Lấy ảnh nền
        template = get_template()
        if not template:
            _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được ảnh nền")
            return
        
        w, h = template.size

        frame_w = int(w * 0.6)
        frame_h = int(h * 0.6)
        frame_x = (w - frame_w) // 2
        frame_y = (h - frame_h) // 2
        
        # Cắt ảnh vừa khung
        avatar_fitted = resize_fill_crop(avatar, frame_w, frame_h)
        
        # Dán lên ảnh nền (không bo tròn, dán chồng trực tiếp)
        template.paste(avatar_fitted, (frame_x, frame_y))
        
        # Gửi ảnh
        output_path = os.path.join(CACHE_PATH, f"result_{int(time.time())}.png")
        template.save(output_path)
        client.sendLocalImage(output_path, thread_id=thread_id, thread_type=thread_type)
        os.remove(output_path)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def LIGHT():
    return {"anhtho": handle_anhtho}