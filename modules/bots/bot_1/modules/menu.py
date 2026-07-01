# modules/menu.py
# -*- coding: utf-8 -*-
import os
import importlib
import json
import time
import random
from datetime import datetime
from pathlib import Path
from io import BytesIO

from zlapi.models import Message, MultiMsgStyle, MessageStyle
from PIL import Image, ImageDraw, ImageFilter

from modules.functions.services.artistcore.font.fontLibs import *

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Hiển thị danh sách lệnh",
    "power": "User"
}

# ============================================================
# CẤU HÌNH
# ============================================================
W = 1400
H = 820
PAD = 40

bg_top = (14, 18, 30)
bg_bot = (8, 10, 18)
glass_fill = (255, 255, 255, 28)

white = (245, 248, 255)
lightgray = (180, 190, 215)
dimgray = (150, 160, 190)

CACHE_DIR = Path("assets/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache background để tăng tốc
_bg_cache = None
_bg_size = None

# ============================================================
# HÀM TẠO HIỆU ỨNG (TỐI ƯU)
# ============================================================

def GetCachedBackground(w, h):
    """Lấy background từ cache để tăng tốc"""
    global _bg_cache, _bg_size
    if _bg_cache is not None and _bg_size == (w, h):
        return _bg_cache.copy()
    
    # Tạo nền gradient
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    
    # Tạo gradient nhanh hơn bằng cách vẽ từng dòng
    for y in range(h):
        t = y / (h - 1)
        r = int(bg_top[0] * (1 - t) + bg_bot[0] * t)
        g = int(bg_top[1] * (1 - t) + bg_bot[1] * t)
        b = int(bg_top[2] * (1 - t) + bg_bot[2] * t)
        d.line((0, y, w, y), fill=(r, g, b))
    
    img = img.convert("RGBA")
    
    # Blobs
    layer = Image.new("RGBA", img.size)
    ld = ImageDraw.Draw(layer)
    for _ in range(5):
        rr = random.randint(300, 500)
        x = random.randint(-200, w)
        y = random.randint(-200, h)
        ld.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 50),
            (190, 120, 255, 45),
            (120, 255, 200, 40),
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(100)))
    
    # Noise nhẹ
    noise = Image.new("L", (w, h))
    px = noise.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(125, 135)
    img.alpha_composite(Image.merge("RGBA", (noise, noise, noise, Image.new("L", (w, h), 14))))
    
    _bg_cache = img
    _bg_size = (w, h)
    return img.copy()

def GlassEffect(canvas, box, radius=36, alpha=glass_fill, blur=20, aa=3):
    """Hiệu ứng kính mờ tối ưu"""
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    
    # Giảm blur để tăng tốc
    blurimg = canvas.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blurimg, Image.new("RGBA", (bw, bh), alpha))
    
    # Mask bo tròn
    aa = min(aa, 3)  # Giảm aa để tăng tốc
    mw, mh = bw * aa, bh * aa
    rr = int(min(radius, bw // 2, bh // 2) * aa)
    mask = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, mw, mh), rr, fill=255)
    mask = mask.resize((bw, bh), Image.LANCZOS)
    
    canvas.paste(layer, box, mask)

def FitText(draw, text, font, maxw):
    """Cắt text nếu quá dài"""
    text = str(text or "")
    if not text:
        return ""
    if draw.textlength(text, font=font) <= maxw:
        return text
    ell = "..."
    lim = maxw - draw.textlength(ell, font=font)
    if lim <= 0:
        return ""
    out = ""
    for ch in text:
        if draw.textlength(out + ch, font=font) > lim:
            break
        out += ch
    return out + ell

def GetTextHeight(font):
    """Lấy chiều cao font nhanh"""
    try:
        bbox = font.getbbox("Ag")
        return bbox[3] - bbox[1]
    except:
        return font.getsize("Ag")[1] if hasattr(font, 'getsize') else 40

def CenterY(y1, y2, font):
    """Căn giữa theo chiều dọc"""
    h = GetTextHeight(font)
    return y1 + (y2 - y1 - h) // 2

# ============================================================
# LẤY DANH SÁCH LỆNH (CÓ CACHE)
# ============================================================
_cmd_cache = None
_cmd_cache_time = 0
_CMD_CACHE_TTL = 60  # Cache 60 giây

def get_all_commands():
    """Lấy tất cả lệnh từ modules (có cache)"""
    global _cmd_cache, _cmd_cache_time
    
    now = time.time()
    if _cmd_cache is not None and (now - _cmd_cache_time) < _CMD_CACHE_TTL:
        return _cmd_cache
    
    commands = {}
    modules_dir = "modules"
    
    if not os.path.exists(modules_dir):
        return commands
    
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and filename != '__init__.py' and filename not in ['sleep.py', 'startwith.py']:
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'modules.{module_name}')
                if hasattr(module, 'Kryzis'):
                    light_func = getattr(module, 'Kryzis')
                    if callable(light_func):
                        cmds = light_func()
                        if isinstance(cmds, dict):
                            for cmd_name in cmds.keys():
                                if cmd_name and not cmd_name.isdigit():
                                    commands[cmd_name] = []
            except:
                pass
    
    _cmd_cache = dict(sorted(commands.items()))
    _cmd_cache_time = now
    return _cmd_cache

# ============================================================
# VẼ ẢNH MENU (TỐI ƯU)
# ============================================================

def DrawMenu(commands, out_path, page=1, per_page=18):
    """Vẽ ảnh menu tối ưu"""
    cmd_list = list(commands.keys())
    total = len(cmd_list)
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    page_cmds = cmd_list[start:end]
    
    # Lấy background từ cache
    img = GetCachedBackground(W, H)
    
    # Card chính
    GlassEffect(img, (PAD, PAD, W - PAD, H - PAD), radius=32, alpha=glass_fill, blur=20, aa=3)
    
    d = ImageDraw.Draw(img)
    
    # ── FONT ──────────────────────────────────────────────────
    title_font = FontLib.Load("Dela-gothic-one.ttf", 44)
    sub_font = FontLib.Load("Darley-sans.otf", 22)
    num_font = FontLib.Load("Dela-gothic-one.ttf", 26)
    cmd_font = FontLib.Load("Dela-gothic-one.ttf", 30)
    pref_font = FontLib.Load("Darley-sans.otf", 18)
    nav_font = FontLib.Load("Dela-gothic-one.ttf", 20)
    
    # ── TIÊU ĐỀ ──────────────────────────────────────────────
    title_y = PAD + 20
    title = "DANH SÁCH LỆNH"
    tw = d.textlength(title, font=title_font)
    d.text(((W - tw) // 2, title_y), title, font=title_font, fill=white)
    
    # ── THÔNG TIN TRANG ──────────────────────────────────────
    info_y = title_y + GetTextHeight(title_font) + 16
    page_info = f"Trang {page}/{total_pages}  •  Tổng {total} lệnh"
    piw = d.textlength(page_info, font=sub_font)
    d.text(((W - piw) // 2, info_y), page_info, font=sub_font, fill=dimgray)
    
    # ── KHU VỰC DANH SÁCH ────────────────────────────────────
    header_h = info_y + GetTextHeight(sub_font) + 28
    footer_h = 50
    
    list_y1 = header_h
    list_y2 = H - PAD - footer_h
    list_h = list_y2 - list_y1
    
    # Cấu hình grid
    cols = 3
    rows = 6
    gap_x = 20
    gap_y = 12
    
    list_x1 = PAD + 32
    list_x2 = W - PAD - 32
    list_w = list_x2 - list_x1
    
    item_w = (list_w - (cols - 1) * gap_x) // cols
    item_h = (list_h - (rows - 1) * gap_y) // rows
    item_h = min(item_h, 72)
    item_h = max(item_h, 60)
    
    # Lấy prefix
    from asset.config import PREFIX
    
    # ── VẼ TỪNG ITEM ──────────────────────────────────────────
    for i, cmd in enumerate(page_cmds):
        col = i % cols
        row = i // cols
        
        x1 = list_x1 + col * (item_w + gap_x)
        y1 = list_y1 + row * (item_h + gap_y)
        x2 = x1 + item_w
        y2 = y1 + item_h
        
        # Item background (glass nhẹ)
        GlassEffect(img, (x1, y1, x2, y2), radius=12, alpha=(255, 255, 255, 14), blur=10, aa=2)
        
        # ── SỐ THỨ TỰ (căn trái) ──
        idx = start + i + 1
        num_text = f"{idx:02d}"
        num_w = d.textlength(num_text, font=num_font)
        num_x = x1 + 16
        num_y = CenterY(y1, y2, num_font)
        d.text((num_x, num_y), num_text, font=num_font, fill=dimgray)
        
        # ── TÊN LỆNH (căn giữa) ──
        pref_text = f"{PREFIX}{cmd}"
        pref_w = d.textlength(pref_text, font=pref_font)
        
        # Tính vị trí để căn giữa tên lệnh
        cmd_x = num_x + num_w + 14
        cmd_max_w = x2 - cmd_x - pref_w - 20
        cmd_text = FitText(d, cmd, cmd_font, cmd_max_w)
        cmd_w = d.textlength(cmd_text, font=cmd_font)
        
        # Căn giữa tên lệnh trong khoảng còn lại
        total_space = (x2 - 16) - cmd_x - pref_w
        if total_space > cmd_w + pref_w:
            # Căn giữa
            offset = (total_space - cmd_w - pref_w) // 2
            cmd_x += offset
        
        cmd_y = CenterY(y1, y2, cmd_font)
        d.text((cmd_x, cmd_y), cmd_text, font=cmd_font, fill=white)
        
        # ── PREFIX (căn phải) ──
        pref_x = x2 - pref_w - 14
        pref_y = CenterY(y1, y2, pref_font)
        d.text((pref_x, pref_y), pref_text, font=pref_font, fill=lightgray)
    
    # ── PHÂN TRANG ────────────────────────────────────────────
    if total_pages > 1:
        nav_y = H - PAD - 18
        
        # Previous
        if page > 1:
            prev_text = "◀ Trước"
            pw = d.textlength(prev_text, font=nav_font)
            d.text((PAD + 32, nav_y), prev_text, font=nav_font, fill=lightgray)
        
        # Page number
        page_text = f"{page} / {total_pages}"
        ptw = d.textlength(page_text, font=nav_font)
        d.text(((W - ptw) // 2, nav_y), page_text, font=nav_font, fill=white)
        
        # Next
        if page < total_pages:
            next_text = "Sau ▶"
            nw = d.textlength(next_text, font=nav_font)
            d.text((W - PAD - 32 - nw, nav_y), next_text, font=nav_font, fill=lightgray)
    
    # Lưu ảnh (tối ưu)
    img.save(out_path, "PNG", optimize=True, compress_level=4)
    return out_path, W, H

# ============================================================
# XỬ LÝ LỆNH MENU
# ============================================================

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _sty_success(text):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color="#15A85F", auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text, sty=None):
    if sty is None:
        sty = _sty
    client.replyMessage(Message(text=text, style=sty(text)), msg_obj, thread_id=tid, thread_type=ttype)

def handle_menu(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh menu"""
    commands = get_all_commands()
    
    if not commands:
        _reply(client, message_object, thread_id, thread_type, "❌ Không có lệnh")
        return
    
    # Kiểm tra phân trang
    parts = message.split()
    page = 1
    if len(parts) > 1 and parts[1].isdigit():
        page = int(parts[1])
    
    per_page = 18
    
    # Tạo ảnh
    cache_path = CACHE_DIR / f"menu_{int(time.time())}.png"
    
    try:
        start_time = time.time()
        out_path, w, h = DrawMenu(commands, str(cache_path), page=page, per_page=per_page)
        print(f"[MENU] Tạo ảnh trong {time.time() - start_time:.2f}s")
        
        # Gửi ảnh
        client.sendLocalImage(
            out_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=""),
            width=w,
            height=h
        )
        
        # Xóa ảnh cache
        try:
            os.remove(out_path)
        except:
            pass
            
    except Exception as e:
        print(f"[MENU] Lỗi: {e}")
        # Fallback text
        cmd_list = list(commands.keys())
        total = len(cmd_list)
        total_pages = max(1, (total + per_page - 1) // per_page)
        
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
            
        start = (page - 1) * per_page
        end = min(start + per_page, total)
        
        lines = ["📋 DANH SÁCH LỆNH"]
        for i, cmd in enumerate(cmd_list[start:end], start + 1):
            lines.append(f"{i:02d}. {cmd}")
        
        lines.append(f"\n📄 Trang {page}/{total_pages}  •  Tổng {total} lệnh")
        if total_pages > 1:
            lines.append("💡 Dùng: menu [số trang]")
        
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines), _sty_success)

def Kryzis():
    return {"menu": handle_menu}