# modules/fkbill.py
# -*- coding: utf-8 -*-
import os
import uuid
import json
import urllib.parse
import requests
import qrcode
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from pyzbar.pyzbar import decode


des = {
    "version": "1.0.4",
    "credits": "Kryzis",
    "description": "Tạo bill MB giả (reply QR tự động nhận diện)",
    "power": "USER"
}

CACHE_DIR = "modules/cache/fkbill"
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

def get_font(size, bold=False):
    fonts = [
        "/storage/emulated/0/Download/kryzis/font.ttf",
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/Roboto-Bold.ttf",
        "/system/fonts/NotoSans-Regular.ttf",
    ]
    for f in fonts:
        try:
            if os.path.exists(f):
                return ImageFont.truetype(f, size)
        except:
            pass
    return ImageFont.load_default()

def format_money(value):
    return f"{int(value):,} VND".replace(",", ".")

def draw_center(draw, w, y, text, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (w - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=color)

def create_bill_normal(money, time_str, name, stk, content):
    img = Image.open("mb.png").convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    font_money = get_font(90, bold=True)
    font_time = get_font(40)
    font_name = get_font(60, bold=True)
    font_stk = get_font(36)
    
    draw_center(draw, w, 650, format_money(money), font_money, (33, 33, 200))
    draw_center(draw, w, 780, time_str, font_time, (120, 120, 120))
    draw_center(draw, w, 1080, name.upper(), font_name, (37, 45, 66))
    draw_center(draw, w, 1230, stk, font_stk, (37, 45, 66))
    draw_center(draw, w, 1290, content, font_stk, (37, 45, 66))
    
    path = os.path.join(CACHE_DIR, f"{uuid.uuid4().hex}.png")
    img.save(path)
    return path

def create_bill_with_qr(money, time_str, name, qr_content, content):
    img = Image.open("mb.png").convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    font_money = get_font(90, bold=True)
    font_time = get_font(40)
    font_name = get_font(60, bold=True)
    font_label = get_font(28, bold=True)
    
    draw_center(draw, w, 650, format_money(money), font_money, (33, 33, 200))
    draw_center(draw, w, 780, time_str, font_time, (120, 120, 120))
    draw_center(draw, w, 1080, name.upper(), font_name, (37, 45, 66))
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(qr_content)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((220, 220), Image.Resampling.LANCZOS)
    
    qr_x = (w - 220) // 2
    qr_y = 1180
    img.paste(qr_img, (qr_x, qr_y))
    
    draw_center(draw, w, qr_y + 230, content, font_label, (200, 50, 50))
    
    path = os.path.join(CACHE_DIR, f"{uuid.uuid4().hex}.png")
    img.save(path)
    return path

def handle_fkbill(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type,
               "📖 CÁCH DÙNG:\n"
               "1. Số tài khoản: fkbill <tiền> | <giờ> | <tên> | <stk> | <nội dung>\n"
               "2. QR code: Reply tin nhắn có ảnh QR + fkbill <tiền> | <giờ> | <tên> | <nội dung>\n"
               "VD1: fkbill 500000 | 14:20 | NGUYEN VAN A | 123456 | chuyen tien\n"
               "VD2: (reply ảnh QR) fkbill 500000 | 14:20 | NGUYEN VAN A | chuyen tien")
        return
    
    # Lấy ảnh từ tin nhắn được reply
    qr_content = None
    
    if message_object.quote:
        try:
            # DEBUG
            print(f"[DEBUG] Có reply, quote: {message_object.quote}")
            
            # Cách 1: Lấy từ attach
            if hasattr(message_object.quote, 'attach') and message_object.quote.attach:
                print(f"[DEBUG] attach: {message_object.quote.attach}")
                attach_data = json.loads(message_object.quote.attach)
                media_url = attach_data.get('hdUrl') or attach_data.get('href')
                
                if media_url:
                    media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
                    print(f"[DEBUG] media_url: {media_url}")
                    
                    # Tải ảnh
                    response = requests.get(media_url, timeout=10)
                    img = Image.open(io.BytesIO(response.content))
                    
                    # Decode QR
                    decoded = decode(img)
                    if decoded:
                        qr_content = decoded[0].data.decode('utf-8')
                        print(f"[DEBUG] QR content: {qr_content[:100]}")
                        _reply(client, message_object, thread_id, thread_type, f"✅ Đã nhận diện QR code!")
            
            # Cách 2: Nếu có attachments
            elif hasattr(message_object.quote, 'attachments') and message_object.quote.attachments:
                print(f"[DEBUG] attachments: {message_object.quote.attachments}")
                for att in message_object.quote.attachments:
                    media_url = att.get('hdUrl') or att.get('href') or att.get('url')
                    if media_url:
                        response = requests.get(media_url, timeout=10)
                        img = Image.open(io.BytesIO(response.content))
                        decoded = decode(img)
                        if decoded:
                            qr_content = decoded[0].data.decode('utf-8')
                            break
            
            # Cách 3: Nếu có media
            elif hasattr(message_object.quote, 'media') and message_object.quote.media:
                print(f"[DEBUG] media: {message_object.quote.media}")
                media_url = message_object.quote.media.get('url') or message_object.quote.media.get('hdUrl')
                if media_url:
                    response = requests.get(media_url, timeout=10)
                    img = Image.open(io.BytesIO(response.content))
                    decoded = decode(img)
                    if decoded:
                        qr_content = decoded[0].data.decode('utf-8')
                        
        except Exception as e:
            print(f"[DEBUG] Lỗi đọc QR: {e}")
            import traceback
            traceback.print_exc()
    
    args = " ".join(parts[1:]).split("|")
    args = [a.strip() for a in args]
    
    # Chế độ QR (có nội dung QR từ reply)
    if qr_content:
        if len(args) != 4:
            _reply(client, message_object, thread_id, thread_type, 
                   f"❌ Reply QR cần 4 tham số, bạn nhập {len(args)} tham số.\n"
                   "Cú pháp: fkbill <tiền> | <giờ> | <tên> | <nội dung>\n"
                   "VD: fkbill 500000 | 14:20 | NGUYEN VAN A | chuyen tien")
            return
        
        try:
            money = float(args[0].replace(",", "").strip())
            time_str = args[1].strip()
            name = args[2].strip().upper()
            content = args[3].strip()
            time_full = f"{time_str} - {datetime.now().strftime('%d/%m/%Y')}"
            
            img_path = create_bill_with_qr(money, time_full, name, qr_content, content)
            client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type)
            os.remove(img_path)
            
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ Lỗi: {str(e)}")
    
    # Chế độ số tài khoản thường
    else:
        if len(args) != 5:
            _reply(client, message_object, thread_id, thread_type, 
                   f"❌ Cần 5 tham số, bạn nhập {len(args)} tham số.\n"
                   "Cú pháp: fkbill <tiền> | <giờ> | <tên> | <stk> | <nội dung>\n"
                   "Hoặc reply ảnh QR: fkbill <tiền> | <giờ> | <tên> | <nội dung>\n"
                   "VD: fkbill 500000 | 14:20 | NGUYEN VAN A | 123456 | chuyen tien")
            return
        
        try:
            money = float(args[0].replace(",", "").strip())
            time_str = args[1].strip()
            name = args[2].strip().upper()
            stk = args[3].strip()
            content = args[4].strip()
            time_full = f"{time_str} - {datetime.now().strftime('%d/%m/%Y')}"
            
            img_path = create_bill_normal(money, time_full, name, stk, content)
            client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type)
            os.remove(img_path)
            
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ Lỗi: {str(e)}")

def LIGHT():
    return {"fkbill": handle_fkbill}
