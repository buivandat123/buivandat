# modules/stkquat.py
# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
import requests
import time
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tạo sticker quạt gió từ ảnh (reply ảnh)",
    "power": "USER"
}

CACHE_DIR = "modules/cache/stkquat"
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
            r = requests.post('https://catbox.moe/user/api.php', files={'fileToUpload': f}, data={'reqtype': 'fileupload'}, timeout=60)
            if r.status_code == 200 and r.text.startswith('https://'):
                return r.text.strip()
    except:
        pass
    return None

def upload_to_uguu(file_path):
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://uguu.se/upload', files={'files[]': f}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                if data.get('success'):
                    return data['files'][0]['url']
    except:
        pass
    return None

def create_quat_sticker(img):
    """Tạo sticker quạt gió xoay"""
    # Resize
    img = img.resize((512, 512), Image.LANCZOS)
    
    # Bo tròn
    mask = Image.new("L", (512, 512), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 512, 512), fill=255)
    img.putalpha(mask)
    
    # Tạo hiệu ứng quạt gió (xoay + glow)
    frames = []
    
    for i in range(12):
        # Xoay ảnh
        angle = (i / 12) * 360
        frame = img.rotate(angle, expand=False, resample=Image.BICUBIC)
        
        # Tạo glow
        glow = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        
        # Viền sáng
        for r in range(10, 35, 5):
            alpha = max(0, 120 - r * 3)
            if alpha > 0:
                gdraw.ellipse((r, r, 512-r, 512-r), 
                             outline=(255, 255, 255, alpha), width=2)
        
        # Kết hợp
        frame = Image.alpha_composite(frame, glow)
        frames.append(frame)
    
    return frames

def handle_stkquat(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    # Kiểm tra reply (cách lấy giống stk cũ)
    if not message_object.quote or not message_object.quote.attach:
        _reply(client, message_object, thread_id, thread_type, f"Reply ảnh + {PREFIX}stkquat")
        return
    
    _reply(client, message_object, thread_id, thread_type, f"⏳ Đang tạo sticker quạt gió...")
    
    temp_output = None
    
    try:
        attach_data = json.loads(message_object.quote.attach)
        img_url = attach_data.get('href')
        
        if not img_url and 'params' in attach_data:
            try:
                params = json.loads(attach_data['params'])
                img_url = params.get('hd') or params.get('url')
            except:
                pass
        
        if not img_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy ảnh")
            return
        
        img_url = urllib.parse.unquote(img_url.replace("\\/", "/"))
        if 'jxl' in img_url:
            img_url = img_url.replace('jxl', 'jpg')
        
        # Tải ảnh
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(img_url, timeout=20, headers=headers)
        if r.status_code != 200:
            _reply(client, message_object, thread_id, thread_type, "❌ Tải ảnh thất bại")
            return
        
        # Xử lý ảnh
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        
        # Tạo sticker quạt gió
        frames = create_quat_sticker(img)
        
        # Lưu
        temp_output = os.path.join(CACHE_DIR, f"out_{int(time.time())}.webp")
        frames[0].save(temp_output, save_all=True, append_images=frames[1:],
                      duration=50, loop=0, format="WEBP", quality=85)
        
        # Upload
        url = upload_to_catbox(temp_output)
        if not url:
            url = upload_to_uguu(temp_output)
        
        if url:
            client.sendCustomSticker(staticImgUrl=url, animationImgUrl=url,
                                    thread_id=thread_id, thread_type=thread_type,
                                    width=512, height=512)
        else:
            _reply(client, message_object, thread_id, thread_type, "❌ Upload thất bại")
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")
    finally:
        if temp_output and os.path.exists(temp_output):
            os.remove(temp_output)

def LIGHT():
    return {"stkquat": handle_stkquat}