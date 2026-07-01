# -*- coding: utf-8 -*-
import os
import requests
import tempfile
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_owner

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Đổi avatar bot bằng cách reply ảnh",
    'power': "Owner"
}

def style_warning(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#F7B503", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def style_success(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#15A85F", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def style_error(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#DB342E", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def extract_image_url(obj):
    """Lấy URL ảnh từ message quote"""
    if not obj:
        return None
    if isinstance(obj, str):
        try:
            import json
            obj = json.loads(obj)
        except:
            if obj.startswith('http'):
                return obj
            return None
    if isinstance(obj, dict):
        for k in ['hdUrl', 'normalUrl', 'oriUrl', 'thumbUrl', 'thumb', 'href', 'url']:
            v = obj.get(k)
            if v and isinstance(v, str) and v.startswith('http'):
                # Chuyển jxl/jx sang jpg
                v_lower = v.lower()
                if '.jxl' in v_lower:
                    v = v.replace('.jxl', '.jpg')
                elif '.jx' in v_lower:
                    v = v.replace('.jx', '.jpg')
                if '/jxl/' in v_lower:
                    v = v.replace('/jxl/', '/jpg/')
                return v
        return None
    return None

def download_image(url):
    """Tải ảnh từ URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, timeout=30, headers=headers)
    response.raise_for_status()
    
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name

def handle_setavt(message, message_object, thread_id, thread_type, author_id, client):
    # Chỉ owner mới được đổi avatar bot
    if not is_owner(author_id):
        msg = "ERROR\n    Bạn không có quyền!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return

    # Kiểm tra có reply tin nhắn không
    quote = None
    for attr in ('quote', 'replyMsg', 'reply', 'refMsg', 'quotedMsg'):
        q = getattr(message_object, attr, None)
        if q is not None:
            quote = q
            break

    if quote is None:
        msg = f"WARNING\n    {PREFIX}setavt (reply vào ảnh cần đổi)"
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)
        return

    # Lấy URL ảnh từ tin nhắn được reply
    img_url = None
    for src in (getattr(quote, 'attach', None), getattr(quote, 'msg', None), getattr(quote, 'content', None)):
        if src:
            img_url = extract_image_url(src)
            if img_url:
                break

    if not img_url:
        msg = "ERROR\n    Không tìm thấy ảnh trong tin nhắn được reply!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return

    try:
        # Tải ảnh về
        temp_path = download_image(img_url)
        
        # Đổi avatar
        result = client.changeAccountAvatar(temp_path)
        
        # Xóa file tạm
        os.unlink(temp_path)
        
        if result:
            msg = "SUCCESS\n    Đã đổi avatar bot thành công!"
            client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
        else:
            msg = "ERROR\n    Đổi avatar thất bại!"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
            
    except Exception as e:
        msg = f"ERROR\n    {str(e)[:50]}"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)

def Kryzis():
    return {'setavt': handle_setavt}