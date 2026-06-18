# modules/stkai.py - Tạo sticker AI từ text
# -*- coding: utf-8 -*-
import requests
import json
import time
import os
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
API_KEY = "YOUR_API_KEY"  # Thay bằng key của bạn
API_URL = "https://api.segmind.com/workflows/66d1c6bf7d2d7d898909ffec-v10"

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
                         headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'})
        
        if r.status_code != 200:
            _reply(client, message_object, thread_id, thread_type, "❌ Lỗi API")
            return
        
        result = r.json()
        poll_url = result.get('poll_url')
        
        if not poll_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được poll_url")
            return
        
        # Poll chờ kết quả
        for _ in range(30):  # Tối đa 30 lần (khoảng 3 phút)
            time.sleep(7)
            pr = requests.get(poll_url, headers={'Authorization': f'Bearer {API_KEY}'})
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