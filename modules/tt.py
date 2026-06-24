# modules/tiktok.py (thêm phần tải video)
# -*- coding: utf-8 -*-
import os
import requests
import json
import time
import math
from datetime import datetime
from PIL import Image as PILImage
from zlapi.models import Message
from modules.canvas import *

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Tìm kiếm, xem thông tin và tải video TikTok",
    "power": "Thành viên"
}

CACHE_DIR = "/sdcard/download/kryzis/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_SEARCH = "https://nqduan.id.vn/api/tiktok?action=search&keyword={}&count=12"
BASE_INFO = "https://nqduan.id.vn/api/tiktok?action=info&username={}"
BASE_DOWNLOAD = "https://nqduan.id.vn/api/tiktok?action=download&video_id={}"

def search_tiktok(keyword):
    try:
        url = BASE_SEARCH.format(keyword)
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get('success'):
            return data.get('data', {}).get('videos', [])
    except:
        pass
    return None

def get_user_info(username):
    try:
        url = BASE_INFO.format(username)
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get('success'):
            return data.get('data', {})
    except:
        pass
    return None

def download_video(video_id):
    try:
        url = BASE_DOWNLOAD.format(video_id)
        resp = requests.get(url, timeout=30, stream=True)
        if resp.status_code != 200:
            return None
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

def DrawTikTokCard(videos, page, out_path):
    w, h = 1600, 1100
    pad = 50
    
    img = CreateBackground(w, h)
    card = (pad, pad, w - pad, h - pad)
    Glass(img, card, radius=50)
    
    d = ImageDraw.Draw(img)
    
    title_font = Font(44, bold=True)
    d.text((w//2, pad + 30), "TIKTOK SEARCH", font=title_font, fill=TextTitle, anchor="mm")
    
    items_per_page = 6
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(videos))
    page_videos = videos[start_idx:end_idx]
    
    row_h = 130
    start_y = pad + 110
    
    for i, video in enumerate(page_videos):
        y = start_y + i * row_h
        x1 = pad + 30
        x2 = w - pad - 30
        
        Glass(img, (x1, y, x2, y + row_h - 10), radius=16)
        
        idx = str(start_idx + i + 1)
        idx_font = Font(28, bold=True)
        d.text((x1 + 25, y + 45), idx, font=idx_font, fill=TextDim)
        
        title = video.get('title', 'Unknown')[:50]
        if len(video.get('title', '')) > 50:
            title += "..."
        title_font = Font(30, bold=True)
        d.text((x1 + 70, y + 20), title, font=title_font, fill=TextTitle)
        
        author = video.get('author', {}).get('nickname', 'Unknown')
        author_font = Font(24)
        d.text((x1 + 70, y + 60), f"👤 {author}", font=author_font, fill=TextSub)
        
        stats = f"❤️ {format_number(video.get('digg_count', 0))}  💬 {format_number(video.get('comment_count', 0))}  ▶️ {format_number(video.get('play_count', 0))}"
        stats_font = Font(24)
        d.text((x1 + 70, y + 95), stats, font=stats_font, fill=TextDim)
        
        duration = video.get('duration', 0)
        dur_font = Font(24, bold=True)
        dur_text = f"{duration}s"
        d.text((x2 - 80, y + 45), dur_text, font=dur_font, fill=(255, 200, 100))
        
        # Nút tải
        vid = video.get('video_id', '')
        d.text((x2 - 180, y + 75), f"📥 /dl {vid[:8]}", font=Font(20), fill=(100, 200, 255))
    
    total_pages = math.ceil(len(videos) / items_per_page)
    ctrl_y = h - pad - 55
    ctrl_h = 48
    ctrl_w = 420
    ctrl_x = (w // 2) - (ctrl_w // 2)
    
    Glass(img, (ctrl_x, ctrl_y, ctrl_x + ctrl_w, ctrl_y + ctrl_h), radius=25)
    ctrl_font = Font(26, bold=True)
    d.text((ctrl_x + ctrl_w // 2, ctrl_y + ctrl_h // 2),
           f"Trang {page}/{total_pages}  |  {len(videos)} video",
           font=ctrl_font, fill=TextSub, anchor="mm")
    
    img.save(out_path, "PNG", optimize=True)
    return out_path, w, h

def DrawUserInfoCard(user_data, out_path):
    w, h = 1600, 900
    pad = 50
    
    img = CreateBackground(w, h)
    card = (pad, pad, w - pad, h - pad)
    Glass(img, card, radius=50)
    
    d = ImageDraw.Draw(img)
    
    user = user_data.get('user', {})
    stats = user_data.get('stats', {})
    
    LeftW = 380
    Gap = 35
    Inner = 30
    
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
    avatar_y = Ly1 + 40
    img.paste(avatar, (avatar_x, avatar_y), avatar)
    
    name = user.get('nickname', 'Unknown')
    name_font = Font(34, bold=True)
    name_fit = FitText(d, name, name_font, LeftW - 50)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 25), name_fit, font=name_font, fill=TextTitle, anchor="mm")
    
    username = user.get('uniqueId', '')
    username_font = Font(26)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 65), f"@{username}", font=username_font, fill=TextSub, anchor="mm")
    
    verified = user.get('verified', False)
    if verified:
        d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 100), "✅ Verified", font=Font(24, bold=True), fill=(0, 200, 255), anchor="mm")
    
    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = w - pad - Inner
    
    title_font = Font(44, bold=True)
    d.text(((Rx1 + Rx2) // 2, Ry1 + 35), "THONG TIN", font=title_font, fill=TextTitle, anchor="mm")
    
    info_y = Ry1 + 100
    row_h = 52
    label_font = Font(28, bold=True)
    value_font = Font(28)
    col1_x = Rx1 + 30
    col2_x = Rx1 + 200
    
    info = [
        ("ID", user.get('id', 'Unknown')),
        ("Bio", user.get('signature', 'Khong co bio')[:50] + "..." if len(user.get('signature', '')) > 50 else user.get('signature', 'Khong co bio')),
        ("Following", format_number(stats.get('followingCount', 0))),
        ("Followers", format_number(stats.get('followerCount', 0))),
        ("Likes", format_number(stats.get('heartCount', 0))),
        ("Videos", format_number(stats.get('videoCount', 0))),
    ]
    
    for i, (label, value) in enumerate(info):
        y = info_y + i * row_h
        d.text((col1_x, y), label + ":", font=label_font, fill=TextDim)
        d.text((col2_x, y), value, font=value_font, fill=TextSub)
    
    footer_font = Font(22)
    d.text((w // 2, h - pad - 30), "TikTok Info - Kryzis Bot", font=footer_font, fill=TextDim, anchor="mm")
    
    img.save(out_path, "PNG", optimize=True)
    return out_path, w, h

def handle_tiktok(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        msg = """🎵 TIKTOK

Cách dùng:
• tiktok <từ khóa> - Tìm video
• tiktok info <username> - Xem thông tin user
• tiktok dl <video_id> - Tải video
• tt <số> - Xem trang tiếp theo

Ví dụ:
• tiktok dance
• tiktok info chung.hong4549
• tiktok dl 7644749890215611662
"""
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
        return
    
    # Lệnh info
    if parts[1].lower() == "info":
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Nhập username!\nVD: tiktok info chung.hong4549"), 
                                message_object, thread_id, thread_type, ttl=60000)
            return
        
        username = parts[2]
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
        return
    
    # Lệnh tải video
    if parts[1].lower() in ["dl", "download"]:
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Nhập video_id!\nVD: tiktok dl 7644749890215611662"), 
                                message_object, thread_id, thread_type, ttl=60000)
            return
        
        video_id = parts[2]
        client.replyMessage(Message(text=f"📥 Đang tải video {video_id}..."), 
                            message_object, thread_id, thread_type, ttl=30000)
        
        data = download_video(video_id)
        if not data:
            client.replyMessage(Message(text="❌ Không tìm thấy video!"), 
                                message_object, thread_id, thread_type, ttl=60000)
            return
        
        video_url = data.get('video_url') or data.get('play') or data.get('wmplay')
        if not video_url:
            client.replyMessage(Message(text="❌ Không lấy được link video!"), 
                                message_object, thread_id, thread_type, ttl=60000)
            return
        
        # Tải video về
        filename = os.path.join(CACHE_DIR, f"tt_{video_id}_{int(time.time())}.mp4")
        try:
            resp = requests.get(video_url, stream=True, timeout=60)
            with open(filename, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            
            # Gửi video
            client.sendLocalVideo(filename, thread_id=thread_id, thread_type=thread_type,
                                  message=Message(text=f"🎵 Video {video_id}"))
            
            try:
                os.remove(filename)
            except:
                pass
            
        except Exception as e:
            client.replyMessage(Message(text=f"❌ Lỗi tải: {str(e)[:80]}"), 
                                message_object, thread_id, thread_type, ttl=60000)
        return
    
    # Tìm kiếm
    keyword = " ".join(parts[1:])
    
    client.replyMessage(Message(text=f"🔍 Đang tìm: {keyword}..."), 
                        message_object, thread_id, thread_type, ttl=30000)
    
    videos = search_tiktok(keyword)
    
    if not videos:
        client.replyMessage(Message(text="❌ Không tìm thấy video nào!"), 
                            message_object, thread_id, thread_type, ttl=60000)
        return
    
    if not hasattr(client, '_tt_results'):
        client._tt_results = {}
    client._tt_results[author_id] = {
        'videos': videos,
        'time': time.time()
    }
    
    out_path = os.path.join(CACHE_DIR, f"tt_{int(time.time())}.png")
    DrawTikTokCard(videos, 1, out_path)
    
    with PILImage.open(out_path) as im:
        w, h = im.size
    
    client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type,
                          message=Message(text=f"🎵 Tìm thấy {len(videos)} video\n📝 Nhập 'tt <số>' để xem tiếp\n📥 'tiktok dl <video_id>' để tải"), 
                          width=w, height=h)
    
    try:
        os.remove(out_path)
    except:
        pass

def handle_tt_page(message, message_object, thread_id, thread_type, author_id, client):
    if not message.strip().isdigit():
        return
    
    page = int(message.strip())
    if page < 1:
        page = 1
    
    if not hasattr(client, '_tt_results') or author_id not in client._tt_results:
        client.replyMessage(Message(text="❌ Hết hạn! Tìm kiếm lại với 'tiktok <từ khóa>'"), 
                            message_object, thread_id, thread_type, ttl=60000)
        return
    
    data = client._tt_results[author_id]
    if time.time() - data['time'] > 300:
        del client._tt_results[author_id]
        client.replyMessage(Message(text="❌ Hết hạn! Tìm kiếm lại."), 
                            message_object, thread_id, thread_type, ttl=60000)
        return
    
    videos = data['videos']
    items_per_page = 6
    total_pages = math.ceil(len(videos) / items_per_page)
    
    if page > total_pages:
        page = total_pages
    
    out_path = os.path.join(CACHE_DIR, f"tt_{int(time.time())}.png")
    DrawTikTokCard(videos, page, out_path)
    
    with PILImage.open(out_path) as im:
        w, h = im.size
    
    client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type,
                          message=Message(text=""), width=w, height=h)
    
    try:
        os.remove(out_path)
    except:
        pass

def Kryzis():
    return {
        "tiktok": handle_tiktok,
        "tt": handle_tt_page
    }