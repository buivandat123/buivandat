# modules/stkspin.py
# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
import requests
import time
from PIL import Image, ImageDraw
from io import BytesIO
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "2.0.0",
    "credits": "kryzis X TXA",
    "description": "Tạo sticker xoay từ ảnh/sticker (reply)",
    "power": "USER"
}

CACHE_DIR = "modules/cache/stkspin"
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

def upload_to_catbox(file_path):
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://catbox.moe/user/api.php', files={'fileToUpload': f}, data={'reqtype': 'fileupload'}, timeout=30)
            if r.status_code == 200 and r.text.startswith('https://'):
                return r.text.strip()
    except:
        pass
    return None

def create_rotating_sticker(image_bytes, output_path, direction="phải"):
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        img = img.resize((512, 512), Image.LANCZOS)
        
        # Bo tròn
        mask = Image.new("L", (512, 512), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 512, 512), fill=255)
        img.putalpha(mask)
        
        # Tạo frame xoay
        frames = []
        mult = 1 if direction == "phải" else -1
        for i in range(12):
            angle = (i / 12) * 360 * mult
            frame = img.rotate(angle, expand=False, resample=Image.BICUBIC)
            frames.append(frame)
        
        frames[0].save(output_path, save_all=True, append_images=frames[1:],
                      duration=50, loop=0, format="WEBP", quality=85)
        return True
    except Exception as e:
        print(f"Lỗi tạo sticker: {e}")
        return False

def handle_stkspin(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    if not message_object.quote or not message_object.quote.attach:
        _reply(client, message_object, thread_id, thread_type, f"Reply ảnh/sticker + {PREFIX}stkspin")
        return
    
    direction = "trái" if "trái" in message.lower() else "phải"
    
    _reply(client, message_object, thread_id, thread_type, f"⏳ Đang xử lý...")
    
    try:
        attach_data = json.loads(message_object.quote.attach)
        img_url = attach_data.get('href')
        
        if not img_url and 'params' in attach_data:
            try:
                params = json.loads(attach_data['params'])
                img_url = params.get('hd') or params.get('url')
                if 'webp' in params and 'url' in params['webp']:
                    img_url = params['webp']['url']
            except:
                pass
        
        if not img_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy ảnh")
            return
        
        img_url = urllib.parse.unquote(img_url.replace("\\/", "/"))
        
        # Tải ảnh với headers
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(img_url, timeout=15, headers=headers)
        if r.status_code != 200:
            _reply(client, message_object, thread_id, thread_type, "❌ Tải ảnh thất bại")
            return
        
        # Kiểm tra content type
        content_type = r.headers.get('Content-Type', '')
        if 'image' not in content_type and 'webp' not in content_type:
            # Thử xem có phải sticker không
            if not img_url.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                _reply(client, message_object, thread_id, thread_type, "❌ File không phải ảnh")
                return
        
        # Xử lý trực tiếp từ bytes
        temp_output = os.path.join(CACHE_DIR, f"out_{int(time.time())}.webp")
        
        if create_rotating_sticker(r.content, temp_output, direction):
            url = upload_to_catbox(temp_output)
            if url:
                client.sendCustomSticker(staticImgUrl=url, animationImgUrl=url,
                                        thread_id=thread_id, thread_type=thread_type,
                                        width=512, height=512)
            else:
                _reply(client, message_object, thread_id, thread_type, "❌ Upload thất bại")
        else:
            _reply(client, message_object, thread_id, thread_type, "❌ Tạo sticker thất bại")
        
        if os.path.exists(temp_output):
            os.remove(temp_output)
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def Kryzis():
    return {"stkspin": handle_stkspin}