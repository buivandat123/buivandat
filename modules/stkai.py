# modules/stkai.py
# -*- coding: utf-8 -*-
import os
import json
import requests
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tạo sticker AI từ văn bản",
    "power": "USER"
}

CACHE_DIR = "modules/cache/stkai"
os.makedirs(CACHE_DIR, exist_ok=True)

# API Key Segmind (bạn cần đăng ký lấy key)
API_KEY = "SG_1e34ecddf792d666"  # Thay bằng key của bạn
API_URL = "https://api.segmind.com/workflows/66d1c6bf7d2d7d898909ffec-v10"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def upload_to_catbox(file_path):
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://catbox.moe/user/api.php', 
                            files={'fileToUpload': f}, 
                            data={'reqtype': 'fileupload'}, timeout=60)
            if r.status_code == 200 and r.text.startswith('https://'):
                return r.text.strip()
    except:
        pass
    return None

def handle_stkai(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, 
               f"{PREFIX}stkai <mô tả sticker>\nVD: {PREFIX}stkai cute dog sticker, cartoon style")
        return
    
    prompt = " ".join(parts[1:])
    
    _reply(client, message_object, thread_id, thread_type, f"⏳ Đang tạo sticker AI...")
    
    try:
        # Gửi request tạo ảnh
        data = {"text_prompt": prompt}
        r = requests.post(API_URL, json=data, 
                         headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}, timeout=30)
        
        if r.status_code != 200:
            _reply(client, message_object, thread_id, thread_type, f"❌ API lỗi: {r.status_code}")
            return
        
        result = r.json()
        poll_url = result.get('poll_url')
        
        if not poll_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được poll_url")
            return
        
        # Poll chờ kết quả
        for _ in range(30):  # Tối đa 30 lần (khoảng 3 phút)
            time.sleep(7)
            pr = requests.get(poll_url, headers={'Authorization': f'Bearer {API_KEY}'}, timeout=30)
            pr_data = pr.json()
            
            if pr_data.get('status') == 'COMPLETED':
                outputs = json.loads(pr_data.get('output', '{}'))
                image_url = outputs.get('image_url') or outputs.get('url')
                
                if image_url:
                    # Tải ảnh về
                    img_r = requests.get(image_url, timeout=30)
                    temp_path = os.path.join(CACHE_DIR, f"out_{int(time.time())}.png")
                    with open(temp_path, 'wb') as f:
                        f.write(img_r.content)
                    
                    # Upload lên catbox để gửi sticker
                    sticker_url = upload_to_catbox(temp_path)
                    os.remove(temp_path)
                    
                    if sticker_url:
                        client.sendCustomSticker(staticImgUrl=sticker_url, animationImgUrl=sticker_url,
                                                thread_id=thread_id, thread_type=thread_type,
                                                width=512, height=512)
                    else:
                        _reply(client, message_object, thread_id, thread_type, "❌ Upload thất bại")
                    return
            elif pr_data.get('status') == 'FAILED':
                _reply(client, message_object, thread_id, thread_type, "❌ Tạo sticker thất bại")
                return
        
        _reply(client, message_object, thread_id, thread_type, "❌ Timeout")
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def LIGHT():
    return {"stkai": handle_stkai}