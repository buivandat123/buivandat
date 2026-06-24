# modules/gay.py
# -*- coding: utf-8 -*-
import os
import time
import json
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from zlapi.models import Message
from modules.canvas import *

des = {
    "version": "1.0.0",
    "credits": "kryzis",
    "description": "Tạo ảnh gay từ canvas",
    "power": "User"
}

# ── CẤU HÌNH ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── STYLE CANVAS ──────────────────────────────────────────────────────────
W, H = 900, 680
PAD = 30
Inner = 20

BgTop = (255, 180, 200)   
BgBot = (255, 80, 130)   
TextTitle = (255, 255, 255, 255)
TextSub = (240, 220, 230, 255)
TextDim = (200, 180, 190, 255)
Accent = (255, 50, 100, 255)

# ── HÀM HỖ TRỢ ──────────────────────────────────────────────────────────

def get_avatar(client, uid):
    """Lấy avatar của user"""
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get("avatar", "")
    except:
        return ""

def get_name(client, uid):
    """Lấy tên của user"""
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get("displayName", str(uid))
    except:
        return str(uid)

def LoadImageFromUrl(url, size=None):
    """Tải ảnh từ URL"""
    try:
        import requests
        from io import BytesIO
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if size:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            return img.convert('RGBA')
    except:
        pass
    return Image.new('RGBA', (200, 200), (200, 200, 200, 255))

def DrawProgressBar(draw, x, y, w, h, percent, color_bg, color_fg):
    """Vẽ thanh tiến trình"""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h//2, fill=color_bg)
    if percent > 0:
        pw = int(w * percent / 100)
        draw.rounded_rectangle((x, y, x + pw, y + h), radius=h//2, fill=color_fg)

# ── VẼ ẢNH GAY ──────────────────────────────────────────────────────────

def DrawGayCard(client, uid, out_path):
    """Vẽ ảnh gay từ canvas"""
    
    gay_percent = random.randint(50, 100)
    
    # Tạo background
    img = CreateBackground(W, H)
    
    # Blobs nền (giảm độ đậm)
    layer = Image.new("RGBA", img.size)
    db = ImageDraw.Draw(layer)
    colors = [
        (255, 100, 150, 40),
        (255, 50, 100, 35),
        (200, 50, 150, 30),
        (255, 150, 200, 35)
    ]
    for _ in range(6):
        rr = random.randint(150, 300)
        x = random.randint(-60, W)
        y = random.randint(-60, H)
        db.ellipse((x, y, x + rr, y + rr), fill=random.choice(colors))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(40)))
    
    # ── CARD CHÍNH ──────────────────────────────────────────────────────
    card = (PAD, PAD, W - PAD, H - PAD)
    Glass(img, card, radius=30, alpha=(255, 255, 255, 15))
    
    d = ImageDraw.Draw(img)
    
    # ── HEADER ──────────────────────────────────────────────────────────
    d.text((W // 2, PAD + 20), "GAY PRIDE", font=Font(38, bold=True), fill=Accent, anchor="mm")
    d.line((PAD + 80, PAD + 60, W - PAD - 80, PAD + 60), fill=(255, 255, 255, 30), width=2)
    
    # ── AVATAR GÓC TRÁI (giống menu) ──────────────────────────────────
    avatar_size = 120
    avatar_x = PAD + 40
    avatar_y = PAD + 85
    
    avatar_url = get_avatar(client, uid)
    avatar = LoadImageFromUrl(avatar_url, (400, 400))
    avatar = CircleCrop(avatar, avatar_size)
    
    # Viền trắng quanh avatar (giống menu)
    border_size = 5
    border = Image.new('RGBA', (avatar_size + border_size*2, avatar_size + border_size*2), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.ellipse((0, 0, avatar_size + border_size*2, avatar_size + border_size*2), 
                        fill=(255, 255, 255, 150))
    img.paste(border, (avatar_x - border_size, avatar_y - border_size), border)
    
    # Shadow
    shadow = Image.new('RGBA', (avatar_size + 10, avatar_size + 10), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((5, 5, avatar_size + 5, avatar_size + 5), fill=(0, 0, 0, 50))
    img.paste(shadow, (avatar_x - 5, avatar_y - 3), shadow)
    
    # Paste avatar
    img.paste(avatar, (avatar_x, avatar_y), avatar)
    
    # ── THÔNG TIN BÊN CẠNH AVATAR ────────────────────────────────────
    info_x = avatar_x + avatar_size + 25
    info_y = avatar_y + 5
    
    # Tên
    name = get_name(client, uid)
    d.text((info_x, info_y), name, font=Font(28, bold=True), fill=TextTitle)
    
    # Badge GAY
    badge_y = info_y + 38
    badge_w = 120
    badge_h = 32
    d.rounded_rectangle((info_x, badge_y, info_x + badge_w, badge_y + badge_h), 
                        radius=10, fill=(255, 50, 100, 220))
    d.text((info_x + 60, badge_y + 17), "GAY", font=Font(16, bold=True), 
           fill=(255, 255, 255, 255), anchor="mm")
    
    # ── SỐ THỨ TỰ ──────────────────────────────────────────────────────
    try:
        number = str(int(uid) % 1000000)
        if len(number) < 6:
            number = number.zfill(6)
    except:
        number = str(random.randint(100000, 999999))
    
    id_y = badge_y + 38
    d.text((info_x, id_y), f"#ID: {number}", font=Font(18), fill=TextSub)
    
    # ── GAY RATE ────────────────────────────────────────────────────────
    rate_y = id_y + 32
    d.text((info_x, rate_y), f"GAY RATE: {gay_percent}%", font=Font(20, bold=True), fill=Accent)
    
    # Thanh %
    bar_y = rate_y + 28
    bar_x = info_x
    bar_w = 450
    bar_h = 24
    
    DrawProgressBar(d, bar_x, bar_y, bar_w, bar_h, gay_percent, 
                   (50, 50, 50, 120), (255, 50, 100, 255))
    
    # ── STATUS ──────────────────────────────────────────────────────────
    if gay_percent >= 80:
        status = "dạ, đi chuyển giới đi nhé"
        color = (255, 50, 50)
    elif gay_percent >= 60:
        status = "nhà mình sắp có con gái"
        color = (255, 80, 100)
    elif gay_percent >= 40:
        status = "cu chạm cu"
        color = (100, 150, 255)
    else:
        status = "bê đê thuần"
        color = (100, 200, 255)
    
    status_y = bar_y + bar_h + 12
    d.text((info_x, status_y), f"Status: {status}", font=Font(20, bold=True), fill=color)
    
    # ── FOOTER ──────────────────────────────────────────────────────────
    footer_y = H - PAD - 25
    d.line((PAD + 60, footer_y, W - PAD - 60, footer_y), fill=(255, 255, 255, 25), width=1)
    
    d.text((PAD + 70, footer_y + 8), "❤️ Made with love", font=Font(14), fill=TextDim)
    d.text((W - PAD - 70, footer_y + 8), f"📅 {datetime.now().strftime('%d/%m/%Y')}", 
           font=Font(14), fill=TextDim, anchor="ra")
    
    # ── LƯU ẢNH ──────────────────────────────────────────────────────
    img.save(out_path, "PNG", optimize=True, compress_level=6)
    return out_path

# ── HÀM XỬ LÝ CHÍNH ────────────────────────────────────────────────────

def handle_gay(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh gay"""
    
    target_uid = author_id
    
    if message_object.mentions:
        target_uid = message_object.mentions[0]["uid"]
    else:
        if message_object.quote and message_object.quote.uidFrom:
            target_uid = message_object.quote.uidFrom
    
    try:
        out_path = os.path.join(CACHE_DIR, f"gay_{int(time.time())}_{random.randint(1000, 9999)}.png")
        
        DrawGayCard(client, target_uid, out_path)
        
        with Image.open(out_path) as im:
            w, h = im.size
        
        target_name = get_name(client, target_uid)
        
        client.sendLocalImage(
            out_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=f"🏳️‍🌈 {target_name}"),
            width=w,
            height=h
        )
        
        try:
            os.remove(out_path)
        except:
            pass
        
    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {str(e)[:100]}"),
            message_object, thread_id, thread_type, ttl=60000
        )

def on_message(message, message_object, thread_id, thread_type, client):
    return handle_gay(message, message_object, thread_id, thread_type, None, client)

def Kryzis():
    return {"gay": handle_gay}