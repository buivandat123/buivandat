# modules/menu.py
# -*- coding: utf-8 -*-
import os
import importlib
import random
import hashlib
import requests
import json
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from datetime import datetime
from zlapi.models import Message

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Hiển thị danh sách lệnh (hỗ trợ nhiều trang)",
    "power": "User"
}

W = 1800
H = 1300
PAD = 60

BgTop = (14, 18, 32)
BgBot = (6, 8, 16)

GlassFill = (255, 255, 255, 20)
TextTitle = (246, 248, 255, 255)
TextSub = (188, 196, 220, 255)
TextDim = (150, 158, 186, 255)

CacheDir = "/sdcard/download/kryzis/cache"
os.makedirs(CacheDir, exist_ok=True)

def Font(size, bold=False):
    paths = [
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/DroidSans.ttf",
        "/system/fonts/NotoSans-Regular.ttf"
    ]
    bold_paths = [
        "/system/fonts/Roboto-Bold.ttf",
        "/system/fonts/DroidSans-Bold.ttf",
        "/system/fonts/NotoSans-Bold.ttf"
    ]
    for p in (bold_paths if bold else paths):
        try:
            return ImageFont.truetype(p, int(size))
        except:
            pass
    return ImageFont.load_default()

def FitText(draw, text, font, max_width):
    text = str(text or "")
    if draw.textlength(text, font=font) <= max_width:
        return text
    ell = "..."
    max_w = max_width - draw.textlength(ell, font=font)
    out = ""
    for ch in text:
        if draw.textlength(out + ch, font=font) > max_w:
            break
        out += ch
    return out + ell

def RoundMask(w, h, r, aa=4):
    mw, mh = w * aa, h * aa
    mr = int(min(r, w // 2, h // 2) * aa)
    m = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, mw, mh), mr, fill=255)
    return m.resize((w, h), Image.LANCZOS)

def Glass(img, box, radius=30, alpha=GlassFill, blur=20, aa=4):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    blur = img.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blur, Image.new("RGBA", (bw, bh), alpha))
    mask = RoundMask(bw, bh, radius, aa=aa)
    img.paste(layer, box, mask)

def Gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(
            int(BgTop[0] * (1 - t) + BgBot[0] * t),
            int(BgTop[1] * (1 - t) + BgBot[1] * t),
            int(BgTop[2] * (1 - t) + BgBot[2] * t),
        ))
    return img.convert("RGBA")

def Blobs(img):
    w, h = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(8):
        rr = random.randint(300, 550)
        x = random.randint(-200, w)
        y = random.randint(-200, h)
        d.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 65),
            (190, 120, 255, 58),
            (120, 255, 210, 52),
            (255, 160, 210, 48),
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(130)))

def Noise(img):
    w, h = img.size
    n = Image.new("L", (w, h))
    px = n.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(115, 145)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 16))))

def LoadImage(url, size):
    w, h = size
    def blank():
        img = Image.new("RGBA", (w, h), (40, 45, 60, 255))
        d = ImageDraw.Draw(img)
        d.ellipse((5, 5, w-5, h-5), fill=(80, 100, 150))
        d.ellipse((w//3-15, h//3-10, w//3+5, h//3+10), fill=(255, 255, 255))
        d.ellipse((w*2//3-15, h//3-10, w*2//3+5, h//3+10), fill=(255, 255, 255))
        d.arc((w//3, h//2, w*2//3, h*3//4), 0, 180, fill=(255, 255, 255), width=6)
        return img
    if not url or not isinstance(url, str):
        return blank()
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return blank()
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.content:
            return blank()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize((w, h), Image.LANCZOS)
    except:
        return blank()

def CropSquare(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))

def CircleCrop(img, size):
    img = CropSquare(img).resize((size, size), Image.LANCZOS)
    mask = RoundMask(size, size, size // 2)
    img.putalpha(mask)
    return img

def get_all_commands():
    commands = []
    # Lấy đường dẫn tuyệt đối đến thư mục modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[Menu] Scanning modules in: {current_dir}")
    
    if not os.path.exists(current_dir):
        print(f"[Menu] Directory not found: {current_dir}")
        return commands
    
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename not in ['__init__.py', 'menu.py']:
            module_name = filename[:-3]
            try:
                print(f"[Menu] Loading module: {module_name}")
                module = importlib.import_module(f'modules.{module_name}')
                if hasattr(module, 'LIGHT'):
                    cmds = module.LIGHT()
                    if isinstance(cmds, dict):
                        for cmd_name in cmds.keys():
                            if cmd_name and not cmd_name.isdigit():
                                commands.append(cmd_name)
                                print(f"[Menu] Found command: {cmd_name}")
            except Exception as e:
                print(f"[Menu] Error loading {module_name}: {e}")
    print(f"[Menu] Total commands found: {len(commands)}")
    return sorted(commands)

def DrawMenuCanvas(commands, page, items_per_page, out_path, avatar_url, user_name):
    img = Gradient(W, H)
    Blobs(img)
    Noise(img)

    card = (PAD, PAD, W - PAD, H - PAD)
    Glass(img, card, radius=50)

    d = ImageDraw.Draw(img)

    # BÊN TRÁI: AVATAR NGƯỜI DÙNG
    LeftW = 400
    Gap = 35
    Inner = 30

    Lx1 = PAD + Inner
    Ly1 = PAD + Inner
    Lx2 = Lx1 + LeftW
    Ly2 = H - PAD - Inner

    LeftBox = (Lx1, Ly1, Lx2, Ly2)
    Glass(img, LeftBox, radius=40)

    # Avatar
    avatar_size = 240
    avatar = LoadImage(avatar_url, (500, 500))
    avatar = CircleCrop(avatar, avatar_size)

    avatar_x = Lx1 + (LeftW - avatar_size) // 2
    avatar_y = Ly1 + 60
    img.paste(avatar, (avatar_x, avatar_y), avatar)

    # Tên người dùng
    name_font = Font(36, bold=True)
    name_fit = FitText(d, user_name, name_font, LeftW - 60)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 30), name_fit, font=name_font, fill=TextTitle, anchor="mm")

    # Tổng số lệnh
    total = len(commands)
    total_font = Font(32, bold=True)
    d.text((Lx1 + LeftW // 2, Ly2 - 70), f"{total} COMMANDS", font=total_font, fill=TextDim, anchor="mm")

    # BÊN PHẢI: DANH SÁCH LỆNH
    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = W - PAD - Inner
    Ry2 = Ly2

    title_font = Font(52, bold=True)
    d.text(((Rx1 + Rx2) // 2, Ry1 + 45), "MENU COMMANDS", font=title_font, fill=TextTitle, anchor="mm")

    # 2 cột
    gap = 30
    inner = 22
    right_w = (Rx2 - Rx1 - gap) // 2
    row_h = 75
    start_y = Ry1 + 140
    items_per_col = items_per_page // 2

    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(commands))
    page_commands = commands[start_idx:end_idx]

    for i, cmd in enumerate(page_commands):
        col = i // items_per_col
        row = i % items_per_col
        x1 = Rx1 + inner + col * (right_w + gap)
        y1 = start_y + row * (row_h + 8)
        x2 = x1 + right_w - inner * 2
        y2 = y1 + row_h

        Glass(img, (x1, y1, x2, y2), radius=18)

        name_font = Font(34, bold=True)
        name_fit = FitText(d, cmd, name_font, right_w - 80)
        d.text((x1 + 22, y1 + 24), name_fit, font=name_font, fill=TextTitle)

        idx = str(start_idx + i + 1)
        idx_font = Font(30, bold=True)
        idx_w = d.textlength(idx, font=idx_font)
        d.text((x2 - 28 - idx_w, y1 + 26), idx, font=idx_font, fill=TextDim)

    # ĐIỀU KHIỂN TRANG
    total_pages = math.ceil(len(commands) / items_per_page)
    control_y = H - PAD - 70
    control_h = 60
    control_w = 500
    control_x = (Rx1 + Rx2) // 2 - control_w // 2
    
    Glass(img, (control_x, control_y, control_x + control_w, control_y + control_h), radius=30)
    
    ctrl_font = Font(32, bold=True)
    ctrl_text = f"Trang {page}/{total_pages}  |  Nhap 'menu <so>'"
    d.text((control_x + control_w // 2, control_y + control_h // 2), ctrl_text, 
           font=ctrl_font, fill=TextSub, anchor="mm")
    
    if page > 1:
        prev_x = control_x - 70
        prev_w = 60
        Glass(img, (prev_x, control_y, prev_x + prev_w, control_y + control_h), radius=30)
        d.text((prev_x + prev_w // 2, control_y + control_h // 2), "◀", 
               font=Font(44, bold=True), fill=TextTitle, anchor="mm")
    
    if page < total_pages:
        next_x = control_x + control_w + 10
        next_w = 60
        Glass(img, (next_x, control_y, next_x + next_w, control_y + control_h), radius=30)
        d.text((next_x + next_w // 2, control_y + control_h // 2), "▶", 
               font=Font(44, bold=True), fill=TextTitle, anchor="mm")

    img.save(out_path, "PNG", optimize=True)
    return out_path

def handle_menu(message, message_object, thread_id, thread_type, author_id, client):
    commands = get_all_commands()
    if not commands:
        client.replyMessage(Message(text="Khong co lenh nao!"), message_object, thread_id, thread_type, ttl=60000)
        return
    
    # Phân tích số trang
    parts = message.strip().split()
    page = 1
    items_per_page = 18
    
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
        # Lấy thông tin người dùng
        user_info = client.fetchUserInfo(author_id).changed_profiles.get(str(author_id), {})
        user_name = user_info.get('displayName', 'User')
        avatar_url = user_info.get('avatar', '')
        
        # Tạo cache key THEO USER
        commands_hash = hashlib.md5('|'.join(commands).encode()).hexdigest()[:8]
        cache_key = f"menu_user_{author_id}_page_{page}_{commands_hash}.png"
        cache_path = os.path.join(CacheDir, cache_key)
        
        # Xóa cache cũ của user này (giữ lại tối đa 5 file)
        old_files = [f for f in os.listdir(CacheDir) if f.startswith(f"menu_user_{author_id}_")]
        for old_f in old_files[:-5]:
            try:
                os.remove(os.path.join(CacheDir, old_f))
            except:
                pass
        
        if os.path.exists(cache_path):
            client.sendLocalImage(cache_path, thread_id=thread_id, thread_type=thread_type, message=Message(text=""))
        else:
            DrawMenuCanvas(commands, page, items_per_page, cache_path, avatar_url, user_name)
            client.sendLocalImage(cache_path, thread_id=thread_id, thread_type=thread_type, message=Message(text=""))
                    
    except Exception as e:
        client.replyMessage(Message(text=f"Loi: {str(e)[:80]}"), message_object, thread_id, thread_type, ttl=60000)

def LIGHT():
    return {"menu": handle_menu}