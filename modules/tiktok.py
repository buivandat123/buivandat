# modules/tiktok.py
# -*- coding: utf-8 -*-
import os
import requests
import json
import time
from datetime import datetime
from PIL import Image as PILImage
from zlapi.models import Message
from modules.canvas import *

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Xem thông tin TikTok user",
    "power": "Thành viên"
}

CACHE_DIR = "/sdcard/download/kryzis/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_INFO = "https://nqduan.id.vn/api/tiktok?action=info&username={}"

def get_user_info(username):
    try:
        url = BASE_INFO.format(username)
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                return data.get('data', {})
    except:
        pass
    return None

def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def split_text(draw, text, font, max_width):
    if not text:
        return []
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = ' '.join(current + [w])
        if draw.textlength(test, font=font) <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(' '.join(current))
            current = [w]
    if current:
        lines.append(' '.join(current))
    return lines

def DrawUserInfoCard(user_data, out_path):
    w, h = 1600, 950
    pad = 50
    
    img = CreateBackground(w, h)
    card = (pad, pad, w - pad, h - pad)
    Glass(img, card, radius=50)
    
    d = ImageDraw.Draw(img)
    
    user = user_data.get('user', {})
    stats = user_data.get('stats', {})
    
    # COT TRAI - AVATAR + THONG TIN CA NHAN
    LeftW = 400
    Gap = 30
    Inner = 26
    
    Lx1 = pad + Inner
    Ly1 = pad + Inner
    Lx2 = Lx1 + LeftW
    Ly2 = h - pad - Inner
    
    Glass(img, (Lx1, Ly1, Lx2, Ly2), radius=40)
    
    avatar_size = 200
    avatar_url = user.get('avatarLarger', user.get('avatarMedium', ''))
    avatar = LoadImage(avatar_url, (avatar_size, avatar_size))
    avatar = CircleCrop(avatar, avatar_size)
    
    avatar_x = Lx1 + (LeftW - avatar_size) // 2
    avatar_y = Ly1 + 35
    img.paste(avatar, (avatar_x, avatar_y), avatar)
    
    # Ten
    name = user.get('nickname', 'Unknown')
    name_font = Font(34, bold=True)
    name_fit = FitText(d, name, name_font, LeftW - 50)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 22), name_fit, font=name_font, fill=TextTitle, anchor="mm")
    
    # Username
    username = user.get('uniqueId', '')
    username_font = Font(26)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 60), f"@{username}", font=username_font, fill=TextSub, anchor="mm")
    
    # Verified
    verified = user.get('verified', False)
    if verified:
        d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 95), "✅ Verified", font=Font(24, bold=True), fill=(0, 200, 255), anchor="mm")
    
    # Bio
    signature = user.get('signature', '')
    if signature:
        bio_font = Font(24)
        bio_lines = split_text(d, signature, bio_font, LeftW - 60)
        bio_start = avatar_y + avatar_size + (135 if verified else 110)
        for i, line in enumerate(bio_lines[:3]):
            d.text((Lx1 + LeftW // 2, bio_start + i * 32), line, font=bio_font, fill=TextDim, anchor="mm")
    
    # COT PHAI - STATS
    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = w - pad - Inner
    Ry2 = Ly2
    
    title_font = Font(44, bold=True)
    d.text(((Rx1 + Rx2) // 2, Ry1 + 30), "THONG KE", font=title_font, fill=TextTitle, anchor="mm")
    
    # Stat items - Bỏ icon, chỉ text
    stat_items = [
        {"label": "Followers", "value": format_number(stats.get('followerCount', 0)), "color": (255, 100, 100)},
        {"label": "Following", "value": format_number(stats.get('followingCount', 0)), "color": (100, 200, 255)},
        {"label": "Likes", "value": format_number(stats.get('heartCount', 0)), "color": (255, 100, 200)},
        {"label": "Videos", "value": format_number(stats.get('videoCount', 0)), "color": (100, 255, 150)},
        {"label": "Total Views", "value": format_number(stats.get('totalViews', 0)), "color": (255, 200, 100)},
        {"label": "Engagement", "value": f"{int(stats.get('heartCount', 0) / max(stats.get('followerCount', 1), 1))}%", "color": (200, 150, 255)},
    ]
    
    cols = 3
    gap = 20
    inner = 18
    col_w = (Rx2 - Rx1 - gap * (cols - 1) - 30) // cols
    row_h = 100
    start_y = Ry1 + 90
    
    for i, item in enumerate(stat_items):
        col = i % cols
        row = i // cols
        x1 = Rx1 + 15 + col * (col_w + gap)
        y1 = start_y + row * (row_h + 12)
        x2 = x1 + col_w
        y2 = y1 + row_h
        
        Glass(img, (x1, y1, x2, y2), radius=18)
        color = item["color"]
        
        # Value (to)
        d.text((x1 + col_w // 2, y1 + 25), item["value"], font=Font(38, bold=True), fill=color, anchor="mm")
        
        # Label (nho)
        d.text((x1 + col_w // 2, y1 + 70), item["label"], font=Font(24), fill=TextSub, anchor="mm")
    
    # Footer
    footer_font = Font(22)
    d.text((w // 2, h - pad - 30), "TikTok Info - Kryzis Bot", font=footer_font, fill=TextDim, anchor="mm")
    
    img.save(out_path, "PNG", optimize=True)
    return out_path, w, h

def handle_tiktok(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        msg = """🎵 TIKTOK INFO

Cách dùng: tiktok <username>
Ví dụ: tiktok chung.hong4549
"""
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
        return
    
    username = parts[1].strip()
    if username.startswith('@'):
        username = username[1:]
    
    client.replyMessage(Message(text=f"🔍 Đang lấy thông tin: {username}..."), 
                        message_object, thread_id, thread_type, ttl=30000)
    
    data = get_user_info(username)
    if not data:
        client.replyMessage(Message(text="❌ Không tìm thấy user!"), 
                            message_object, thread_id, thread_type, ttl=60000)
        return
    
    out_path = os.path.join(CACHE_DIR, f"tt_user_{int(time.time())}.png")
    DrawUserInfoCard(data, out_path)
    
    with PILImage.open(out_path) as im:
        w, h = im.size
    
    client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type,
                          message=Message(text=""), width=w, height=h)
    
    try:
        os.remove(out_path)
    except:
        pass

def LIGHT():
    return {"tiktok": handle_tiktok}
