# modules/stkdisc.py
# -*- coding: utf-8 -*-
import requests
import subprocess
import json
import urllib.parse
import os
import threading
import time
import random
import re
import tempfile
import shutil
from io import BytesIO
from PIL import Image, ImageDraw
from zlapi.models import Message

des = {
    'version': "2.0.0",
    'credits': "Hoàng Khánh Premium",
    'description': "Tạo sticker đĩa xoay từ ảnh reply",
    'power': "Thành viên"
}

def get_file_type(url):
    url_lower = url.lower()
    if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
        return "image"
    return "unknown"

def round_corners_fast(img, radius_ratio=0.12):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    radius = max(5, min(int(min(img.size) * radius_ratio), 50))
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    img.putalpha(mask)
    return img

def create_animated_disc_from_image(bg_image, size=512):
    try:
        scale = 2
        work_size = size * scale
        
        w, h = bg_image.size
        if w > h:
            bg_square_src = bg_image.crop(((w - h) // 2, 0, (w - h) // 2 + h, h))
        else:
            bg_square_src = bg_image.crop((0, (h - w) // 2, w, (h - w) // 2 + w))
        
        # Khung vuông bo góc
        square_size = 340 * scale
        square_x = 20 * scale
        square_y = (work_size - square_size) // 2
        square_radius = 40 * scale
        
        square_img = bg_square_src.resize((square_size, square_size), Image.Resampling.LANCZOS)
        
        mask_square = Image.new('L', (square_size, square_size), 0)
        draw_mask_square = ImageDraw.Draw(mask_square)
        draw_mask_square.rounded_rectangle((0, 0, square_size, square_size), radius=square_radius, fill=255)
        
        square_rounded = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
        square_rounded.paste(square_img, (0, 0), mask_square)
        
        # Đĩa xoay
        R_outer = 147 * scale
        R_black = R_outer - 8 * scale
        R_inner = 73 * scale
        
        cx = square_x + square_size
        cy = square_y + square_size // 2
        
        core_size = 2 * R_inner
        bg_core = bg_square_src.resize((core_size, core_size), Image.Resampling.LANCZOS)
        
        disc_size = 2 * R_outer
        disc_base = Image.new('RGBA', (disc_size, disc_size), (0, 0, 0, 0))
        draw_disc = ImageDraw.Draw(disc_base)
        
        draw_disc.ellipse((0, 0, disc_size, disc_size), fill=(120, 120, 125))
        
        black_size = 2 * R_black
        offset_black = (disc_size - black_size) // 2
        draw_disc.ellipse((offset_black, offset_black, offset_black + black_size, offset_black + black_size), fill=(0, 0, 0))
        
        center_size = 20 * scale
        offset_center = (disc_size - center_size) // 2
        draw_disc.ellipse((offset_center, offset_center, offset_center + center_size, offset_center + center_size), fill=(200, 200, 205))
        
        mask_core = Image.new('L', (core_size, core_size), 0)
        draw_mask_core = ImageDraw.Draw(mask_core)
        draw_mask_core.ellipse((0, 0, core_size, core_size), fill=255)
        
        num_frames = 24
        frames = []
        
        for frame_idx in range(num_frames):
            frame = Image.new('RGBA', (work_size, work_size), (0, 0, 0, 0))
            disc_img = disc_base.copy()
            
            angle = - (frame_idx / num_frames) * 360
            rotated_core = bg_core.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
            
            core_with_mask = Image.new('RGBA', (core_size, core_size), (0, 0, 0, 0))
            core_with_mask.paste(rotated_core, (0, 0), mask_core)
            
            core_offset = (disc_size - core_size) // 2
            disc_img.paste(core_with_mask, (core_offset, core_offset), core_with_mask)
            
            frame.paste(disc_img, (cx - R_outer, cy - R_outer), disc_img)
            frame.paste(square_rounded, (square_x, square_y), square_rounded)
            
            frames.append(frame.resize((size, size), Image.Resampling.LANCZOS))
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.webp')
        frames[0].save(
            temp_file.name,
            save_all=True,
            append_images=frames[1:],
            duration=40,
            loop=0,
            format="WEBP",
            quality=75
        )
        return temp_file.name
        
    except Exception as e:
        return None

def process_image(media_url, size):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(media_url, headers=headers, timeout=8)
    response.raise_for_status()
    
    from io import BytesIO
    img = Image.open(BytesIO(response.content))
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    img = round_corners_fast(img)
    return create_animated_disc_from_image(img, size)

def upload_to_catbox(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': ('sticker.webp', f, 'image/webp')}
            response = requests.post('https://catbox.moe/user/api.php', files=files, data={'reqtype': 'fileupload'}, timeout=20)
        if response.status_code == 200 and response.text.startswith('https://'):
            return response.text.strip()
    except:
        pass
    return None

def upload_to_0x0st(file_path):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post('https://0x0.st', files={'file': ('sticker.webp', f, 'image/webp')}, timeout=20)
        if response.status_code == 200:
            url = response.text.strip()
            if url.startswith('https://'):
                return url
    except:
        pass
    return None

def upload_to_tmpfiles(file_path):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': ('sticker.webp', f, 'image/webp')}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('data', {}).get('url'):
                return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except:
        pass
    return None

def upload_to_imgbb(file_path):
    try:
        import base64
        with open(file_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': '6d207e02198a847aa98d0a2a901485a5', 'image': img_data, 'expiration': 600},
            timeout=20
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('url'):
                return data['data']['url']
    except:
        pass
    return None

def upload_file(file_path):
    services = [upload_to_catbox, upload_to_0x0st, upload_to_tmpfiles, upload_to_imgbb]
    for service in services:
        url = service(file_path)
        if url:
            return url
    return None

def handle_stkdisc_command(message, message_object, thread_id, thread_type, author_id, client):
    if not message_object.quote or not message_object.quote.attach:
        client.replyMessage(Message(text="➜ Reply vào ảnh để tạo sticker đĩa xoay."), 
                          message_object, thread_id, thread_type, ttl=60000)
        return

    size = 512
    cmd_text = message.strip().lower()
    size_match = re.search(r'stkdisc\s+(\d+)', cmd_text)
    if size_match:
        size = int(size_match.group(1))
        if size not in [128, 256, 512]:
            size = 512

    try:
        attach_data = json.loads(message_object.quote.attach)
        media_url = attach_data.get('hdUrl') or attach_data.get('href')
        if not media_url:
            client.replyMessage(Message(text="➜ Không tìm thấy URL media."), 
                              message_object, thread_id, thread_type, ttl=60000)
            return

        media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
        if "jxl" in media_url:
            media_url = media_url.replace("jxl", "jpg")

        file_type = get_file_type(media_url)
        if file_type == "unknown":
            client.replyMessage(Message(text="➜ Chỉ hỗ trợ ảnh."), 
                              message_object, thread_id, thread_type, ttl=60000)
            return

    except Exception as e:
        client.replyMessage(Message(text=f"➜ Lỗi: {str(e)[:50]}"), 
                          message_object, thread_id, thread_type, ttl=60000)
        return

    def process_and_send():
        temp_dir = os.path.join(os.path.dirname(__file__), 'cache', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        actual_webp = None
        
        try:
            actual_webp = process_image(media_url, size)
            
            if not actual_webp:
                client.replyMessage(Message(text="➜ Tạo sticker thất bại."), 
                                  message_object, thread_id, thread_type, ttl=60000)
                return
            
            webp_url = upload_file(actual_webp)
            
            if webp_url:
                client.sendCustomSticker(
                    animationImgUrl=webp_url,
                    staticImgUrl=webp_url,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=size,
                    height=size
                )
            else:
                client.replyMessage(Message(text="➜ Upload thất bại."), 
                                  message_object, thread_id, thread_type, ttl=60000)
                
        except Exception as e:
            client.replyMessage(Message(text=f"➜ Lỗi: {str(e)[:50]}"), 
                              message_object, thread_id, thread_type, ttl=60000)
        finally:
            if actual_webp and os.path.exists(actual_webp):
                try:
                    os.remove(actual_webp)
                except:
                    pass
    
    threading.Thread(target=process_and_send, daemon=True).start()

def LIGHT():
    return {'stkdisc': handle_stkdisc_command}