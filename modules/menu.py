# modules/menu.py
# -*- coding: utf-8 -*-
import os
import importlib
import hashlib
import math
from datetime import datetime
from PIL import Image as PILImage
from zlapi.models import Message
from modules.canvas import *

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Hiển thị danh sách lệnh",
    "power": "User"
}

CacheDir = "/sdcard/download/kryzis/cache"
os.makedirs(CacheDir, exist_ok=True)

def get_all_commands():
    commands = []
    current_dir = "/sdcard/download/kryzis/modules"
    if not os.path.exists(current_dir):
        return commands
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename not in ['__init__.py', 'menu.py']:
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'modules.{module_name}')
                if hasattr(module, 'LIGHT'):
                    cmds = module.LIGHT()
                    if isinstance(cmds, dict):
                        for cmd_name in cmds.keys():
                            if cmd_name and not cmd_name.isdigit():
                                commands.append(cmd_name)
            except:
                pass
    return sorted(commands)

def DrawMenuCanvas(commands, page, items_per_page, out_path):
    w, h = 1600, 1000
    pad = 50
    
    img = CreateBackground(w, h)

    card = (pad, pad, w - pad, h - pad)
    Glass(img, card, radius=50)

    d = ImageDraw.Draw(img)

    # COT TRAI - AVATAR
    LeftW = 340
    Gap = 35
    Inner = 28

    Lx1 = pad + Inner
    Ly1 = pad + Inner
    Lx2 = Lx1 + LeftW
    Ly2 = h - pad - Inner

    Glass(img, (Lx1, Ly1, Lx2, Ly2), radius=40)

    avatar_size = 200
    avatar = GetMyAvatar(avatar_size)
    avatar_x = Lx1 + (LeftW - avatar_size) // 2
    avatar_y = Ly1 + 45
    img.paste(avatar, (avatar_x, avatar_y), avatar)

    name_font = Font(32, bold=True)
    name_fit = FitText(d, GetMyName(), name_font, LeftW - 50)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 25), name_fit, font=name_font, fill=TextTitle, anchor="mm")

    total = len(commands)
    total_font = Font(28, bold=True)
    d.text((Lx1 + LeftW // 2, Ly2 - 60), f"{total} COMMANDS", font=total_font, fill=TextDim, anchor="mm")

    # COT PHAI - DANH SACH LENH
    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = w - pad - Inner
    Ry2 = Ly2

    title_font = Font(44, bold=True)
    d.text(((Rx1 + Rx2) // 2, Ry1 + 35), "MENU COMMANDS", font=title_font, fill=TextTitle, anchor="mm")

    gap = 35
    inner = 22
    right_w = (Rx2 - Rx1 - gap) // 2
    row_h = 56
    start_y = Ry1 + 110
    items_per_col = 9
    items_per_page = items_per_col * 2

    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(commands))
    page_commands = commands[start_idx:end_idx]

    for i, cmd in enumerate(page_commands):
        col = i // items_per_col
        row = i % items_per_col
        x1 = Rx1 + inner + col * (right_w + gap)
        y1 = start_y + row * (row_h + 6)
        x2 = x1 + right_w - inner * 2
        y2 = y1 + row_h

        Glass(img, (x1, y1, x2, y2), radius=16)

        cmd_display = cmd[:20] if len(cmd) > 20 else cmd
        cmd_font = Font(28, bold=True)
        d.text((x1 + 18, y1 + 18), cmd_display, font=cmd_font, fill=TextTitle)

        idx = str(start_idx + i + 1)
        idx_font = Font(24, bold=True)
        idx_w = d.textlength(idx, font=idx_font)
        d.text((x2 - 22 - idx_w, y1 + 20), idx, font=idx_font, fill=TextDim)

    # DIEU HUONG TRANG
    total_pages = math.ceil(len(commands) / items_per_page)
    ctrl_y = h - pad - 60
    ctrl_h = 48
    ctrl_w = 420
    ctrl_x = (Rx1 + Rx2) // 2 - ctrl_w // 2

    Glass(img, (ctrl_x, ctrl_y, ctrl_x + ctrl_w, ctrl_y + ctrl_h), radius=25)
    ctrl_font = Font(26, bold=True)
    d.text((ctrl_x + ctrl_w // 2, ctrl_y + ctrl_h // 2),
           f"Trang {page}/{total_pages}  |  Nhap 'menu <so>'",
           font=ctrl_font, fill=TextSub, anchor="mm")

    if page > 1:
        px = ctrl_x - 55
        Glass(img, (px, ctrl_y, px + 48, ctrl_y + ctrl_h), radius=25)
        d.text((px + 24, ctrl_y + ctrl_h // 2), "<",
               font=Font(34, bold=True), fill=TextTitle, anchor="mm")

    if page < total_pages:
        nx = ctrl_x + ctrl_w + 8
        Glass(img, (nx, ctrl_y, nx + 48, ctrl_y + ctrl_h), radius=25)
        d.text((nx + 24, ctrl_y + ctrl_h // 2), ">",
               font=Font(34, bold=True), fill=TextTitle, anchor="mm")

    img.save(out_path, "PNG", optimize=True)
    return out_path, w, h

def handle_menu(message, message_object, thread_id, thread_type, author_id, client):
    commands = get_all_commands()
    if not commands:
        client.replyMessage(Message(text="Khong co lenh nao!"), message_object, thread_id, thread_type, ttl=60000)
        return

    parts = message.strip().split()
    page = 1
    items_per_col = 9
    items_per_page = items_per_col * 2

    if len(parts) > 1:
        try:
            page = int(parts[1])
            if page < 1:
                page = 1
        except:
            pass

    total_pages = math.ceil(len(commands) / items_per_page)
    if page > total_pages:
        page = total_pages

    try:
        commands_hash = hashlib.md5('|'.join(commands).encode()).hexdigest()[:8]
        cache_key = f"menu_page_{page}_{commands_hash}.png"
        cache_path = os.path.join(CacheDir, cache_key)

        if os.path.exists(cache_path):
            with PILImage.open(cache_path) as im:
                w, h = im.size
            client.sendLocalImage(cache_path, thread_id=thread_id, thread_type=thread_type, 
                                  message=Message(text=""), width=w, height=h)
        else:
            DrawMenuCanvas(commands, page, items_per_page, cache_path)
            with PILImage.open(cache_path) as im:
                w, h = im.size
            client.sendLocalImage(cache_path, thread_id=thread_id, thread_type=thread_type, 
                                  message=Message(text=""), width=w, height=h)

            old_files = sorted([f for f in os.listdir(CacheDir) if f.startswith("menu_page_")],
                              key=lambda x: os.path.getmtime(os.path.join(CacheDir, x)))
            for f in old_files[:-10]:
                try:
                    os.remove(os.path.join(CacheDir, f))
                except:
                    pass

    except Exception as e:
        client.replyMessage(Message(text=f"Loi: {str(e)[:80]}"), message_object, thread_id, thread_type, ttl=60000)

def LIGHT():
    return {"menu": handle_menu}
