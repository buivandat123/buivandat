# modules/tiktok.py
# -*- coding: utf-8 -*-
import os
import re
import json
import hashlib
import time
import requests
from datetime import datetime

from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tải video TikTok không logo",
    "power": "User"
}

# ==================== STYLES ====================
def _sty_success(text):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color="#15A85F", auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _sty_error(text):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color="#FF4444", auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _sty_info(text):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color="#FFA500", auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text, sty=None):
    if sty is None:
        sty = _sty_info
    client.replyMessage(Message(text=text, style=sty(text)), msg_obj, thread_id=tid, thread_type=ttype)

# ==================== API TIKTOK ====================

def get_public_url_from_server():
    """Lấy public URL từ web server"""
    try:
        response = requests.get("http://localhost:5000/api/public_url", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('url', '')
    except:
        pass
    return None

# ==================== HANDLER ====================

def handle_tiktok(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh tải video TikTok"""
    try:
        content = message_object.content if hasattr(message_object, 'content') else message
        
        if isinstance(content, dict):
            content = content.get('title', '')
        elif not isinstance(content, str):
            content = str(content)
        
        parts = content.strip().split()
        
        if len(parts) < 2:
            help_text = """📱 **TẢI VIDEO TIKTOK**

📌 **Cách dùng:**
`.tiktok <link_tiktok>`

📌 **Ví dụ:**
`.tiktok https://www.tiktok.com/@user/video/123456789`

⚡ **Tính năng:**
• Tải video về server
• Link xem video ổn định
• Ai cũng xem được"""
            _reply(client, message_object, thread_id, thread_type, help_text, _sty_info)
            return
        
        tiktok_url = parts[1]
        
        if not re.search(r'tiktok\.com', tiktok_url):
            _reply(client, message_object, thread_id, thread_type, 
                   "❌ Link không phải TikTok!", _sty_error)
            return
        
        _reply(client, message_object, thread_id, thread_type,
               "⏳ **Đang tải video...**", _sty_info)
        
        # Gọi API của web server để tải video
        try:
            response = requests.post(
                "http://localhost:5000/api/download",
                json={'url': tiktok_url},
                timeout=60
            )
            
            if response.status_code != 200:
                _reply(client, message_object, thread_id, thread_type,
                       f"❌ Lỗi server: {response.status_code}", _sty_error)
                return
            
            data = response.json()
            
            if data.get('error'):
                _reply(client, message_object, thread_id, thread_type,
                       f"❌ {data['error']}", _sty_error)
                return
            
            # Lấy thông tin
            public_url = get_public_url_from_server() or "http://localhost:5000"
            short_url = data.get('short_url', '')
            short_id = data.get('short_id', '')
            
            duration = data.get('duration', '00:00')
            views = data.get('views', 0)
            likes = data.get('likes', 0)
            comments = data.get('comments', 0)
            
            info_text = f"""📱 **TIKTOK VIDEO**

📹 **Tiêu đề:** {data.get('title', 'Không tiêu đề')[:100]}
👤 **Tác giả:** @{data.get('author', 'Unknown')}
⏱️ **Thời lượng:** {duration}
👁️ **Lượt xem:** {views}
❤️ **Lượt thích:** {likes}
💬 **Bình luận:** {comments}

🔗 **Link xem video:** 
{short_url}

💡 Click link để xem và tải video!"""
            
            _reply(client, message_object, thread_id, thread_type, info_text, _sty_success)
            
        except requests.exceptions.ConnectionError:
            _reply(client, message_object, thread_id, thread_type,
                   "❌ Web server chưa chạy! Vui lòng chạy tiktok_web.py", _sty_error)
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type,
                   f"❌ Lỗi: {str(e)}", _sty_error)
            
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Lỗi: {str(e)}", _sty_error)

# ==================== EXPORT ====================

def Kryzis():
    return {
        "tiktok": handle_tiktok,
        "tt": handle_tiktok
    }