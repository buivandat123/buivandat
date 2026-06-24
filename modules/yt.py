# modules/yt.py
# -*- coding: utf-8 -*-
import requests
import os
import time
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Tải video/audio từ YouTube",
    "power": "Thành viên"
}

CACHE_PATH = "modules/cache/yt"
os.makedirs(CACHE_PATH, exist_ok=True)

API_URL = "https://nqduan.id.vn/api/downall"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def download_file(url, path):
    try:
        r = requests.get(url, stream=True, timeout=60)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except:
        return False

def handle_ytaudio(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, "ytaudio <link YouTube>\nVD: ytaudio https://youtu.be/xxx")
        return
    
    url = parts[1]
    
    _reply(client, message_object, thread_id, thread_type, "⏳ Đang lấy thông tin...")
    
    try:
        res = requests.get(API_URL, params={"url": url}, timeout=30)
        data = res.json()
        
        if not data.get('success'):
            _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được video")
            return
        
        info = data['data']
        title = info['title']
        author = info['author']
        
        # Tìm audio (mp4 quality 360p hoặc thấp nhất)
        audio_url = None
        for m in info['media']:
            if m['type'] == 'video' and m['extension'] == 'mp4':
                audio_url = m['url']
                break
        
        if not audio_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy link tải")
            return
        
        _reply(client, message_object, thread_id, thread_type, f"⏳ Đang tải: {title[:50]}...")
        
        # Tải file
        safe_title = "".join(c for c in title if c.isalnum() or c in ' ._-')[:50]
        path = os.path.join(CACHE_PATH, f"{safe_title}_{int(time.time())}.mp4")
        
        if download_file(audio_url, path):
            # Gửi file
            client.sendLocalFile(path, thread_id=thread_id, thread_type=thread_type,
                                message=Message(text=f"🎵 {title}\n👤 {author}"))
            os.remove(path)
        else:
            _reply(client, message_object, thread_id, thread_type, "❌ Tải thất bại")
            
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def handle_ytvideo(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, "ytvideo <link YouTube>\nVD: ytvideo https://youtu.be/xxx")
        return
    
    url = parts[1]
    
    _reply(client, message_object, thread_id, thread_type, "⏳ Đang lấy thông tin...")
    
    try:
        res = requests.get(API_URL, params={"url": url}, timeout=30)
        data = res.json()
        
        if not data.get('success'):
            _reply(client, message_object, thread_id, thread_type, "❌ Không lấy được video")
            return
        
        info = data['data']
        title = info['title']
        author = info['author']
        
        # Tìm video chất lượng cao nhất
        video_url = None
        for m in info['media']:
            if m['type'] == 'video':
                video_url = m['url']
                quality = m.get('quality', 'unknown')
                break
        
        if not video_url:
            _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy link video")
            return
        
        _reply(client, message_object, thread_id, thread_type, f"⏳ Đang tải: {title[:50]}...")
        
        safe_title = "".join(c for c in title if c.isalnum() or c in ' ._-')[:50]
        path = os.path.join(CACHE_PATH, f"{safe_title}_{int(time.time())}.mp4")
        
        if download_file(video_url, path):
            client.sendLocalVideo(path, thread_id=thread_id, thread_type=thread_type,
                                 message=Message(text=f"📹 {title}\n👤 {author}"))
            os.remove(path)
        else:
            _reply(client, message_object, thread_id, thread_type, "❌ Tải thất bại")
            
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)[:50]}")

def Kryzis():
    return {
        "ytaudio": handle_ytaudio,
        "ytvideo": handle_ytvideo
    }