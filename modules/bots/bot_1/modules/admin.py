# modules/admin.py
# -*- coding: utf-8 -*-
import json
import os
import time
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from modules.canvas import *
from modules.functions.services.artistcore.font.fontLibs import FontLib

des = {"version": "1.0.0", "credits": "kryzis X TXA", "description": "Quản lý admin bot", "power": "Owner"}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETING_FILE = os.path.join(BASE_DIR, "asset", "seting.json")
CACHE_DIR = "/sdcard/download/kryzis/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Các hằng số màu sắc
white = (245, 248, 255)
lightgray = (180, 190, 215)
dimgray = (150, 160, 190)
bgTop = (14, 18, 30)
bgBot = (8, 10, 18)
glassFill = (255, 255, 255, 28)

def _load():
    try:
        with open(SETING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"admin": "", "adm": []}

def _save(s):
    with open(SETING_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def get_owner():
    return str(_load().get("admin", ""))

def get_admins():
    return set(str(x) for x in _load().get("adm", []))

def save_admins(a):
    s = _load()
    s["adm"] = list(a)
    _save(s)

def is_owner(uid):
    return str(uid) == get_owner()

def get_avatar_url(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get("avatar", "")
    except:
        return ""

def get_name(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get("displayName", str(uid))
    except:
        return str(uid)

def _sty(text, color):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _send_mention(client, uid, tid, ttype, header, lines, color):
    name = get_name(client, uid)
    tag = f"@{name}"
    body = "\n".join(f"    {l}" for l in lines)
    text = f"{tag}\n{header}\n{body}"
    info = json.dumps([{"pos": 0, "uid": str(uid), "len": len(tag)}])
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False),
        MessageStyle(offset=len(tag)+1, length=len(header), style="color", color=color, auto_format=False),
        MessageStyle(offset=len(tag)+1, length=len(header), style="bold", auto_format=False),
    ])
    client.sendMentionMessage(Message(text=text, mention=info, style=style), tid)

def _reply_mention(client, msg_obj, tid, ttype, uid, header, lines, color):
    name = get_name(client, uid)
    tag = f"@{name}"
    body = "\n".join(f"    {l}" for l in lines)
    text = f"{tag}\n{header}\n{body}"
    info = json.dumps([{"pos": 0, "uid": str(uid), "len": len(tag)}])
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False),
        MessageStyle(offset=len(tag)+1, length=len(header), style="color", color=color, auto_format=False),
        MessageStyle(offset=len(tag)+1, length=len(header), style="bold", auto_format=False),
    ])
    client.replyMessage(Message(text=text, mention=info, style=style), msg_obj, tid, ttype)

# ============================================================
# HÀM VẼ ẢNH ADMIN LIST (Phong cách giống infoCard + songsCard)
# ============================================================

def GradientBackground(w, h):
    """Tạo nền gradient từ bgTop đến bgBot"""
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(
            int(bgTop[0] * (1 - t) + bgBot[0] * t),
            int(bgTop[1] * (1 - t) + bgBot[1] * t),
            int(bgTop[2] * (1 - t) + bgBot[2] * t),
        ))
    return img.convert("RGBA")

def BlobsEffect(img):
    """Thêm hiệu ứng bóng màu"""
    w, h = img.size
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    for _ in range(6):
        rr = random.randint(300, 520)
        x = random.randint(-200, w)
        y = random.randint(-200, h)
        d.ellipse((x, y, x + rr, y + rr), fill=random.choice([
            (120, 170, 255, 60),
            (190, 120, 255, 55),
            (120, 255, 200, 50),
        ]))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(120)))

def NoiseEffect(img):
    """Thêm hiệu ứng nhiễu"""
    w, h = img.size
    n = Image.new("L", (w, h))
    px = n.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = random.randint(120, 140)
    img.alpha_composite(Image.merge("RGBA", (n, n, n, Image.new("L", (w, h), 18))))

def RoundedMask(bw, bh, radius, aa=4):
    """Tạo mask bo tròn"""
    mw, mh = bw * aa, bh * aa
    rr = int(min(radius, bw // 2, bh // 2) * aa)
    m = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, mw, mh), rr, fill=255)
    return m.resize((bw, bh), Image.LANCZOS)

def GlassEffect(canvas, box, radius=36, alpha=glassFill, blur=26, aa=4):
    """Hiệu ứng kính mờ"""
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    blurimg = canvas.crop(box).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.alpha_composite(blurimg, Image.new("RGBA", (bw, bh), alpha))
    mask = RoundedMask(bw, bh, radius, aa=aa)
    canvas.paste(layer, box, mask)

def CircleCrop(img, size):
    """Cắt ảnh thành hình tròn"""
    if img is None:
        img = Image.new("RGBA", (size, size), (65, 65, 90, 255))
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    return img

def LoadImage(url, size=(200, 200), timeout=10):
    """Tải ảnh từ URL"""
    w, h = size
    def blank():
        return Image.new("RGBA", (w, h), (25, 25, 25, 255))
    if not url or not isinstance(url, str):
        return blank()
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return blank()
    try:
        import requests
        from io import BytesIO
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.content:
            return blank()
        im = Image.open(BytesIO(r.content)).convert("RGBA")
        return im.resize((w, h), Image.LANCZOS)
    except:
        return blank()

def PlaceholderAvatar(size):
    """Tạo avatar placeholder"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Nền
    d.ellipse((0, 0, size, size), fill=(65, 65, 90, 220))
    # Đầu
    head_r = size // 5
    cx = size // 2
    d.ellipse((cx - head_r, size//6, cx + head_r, size//6 + head_r*2), fill=(160, 160, 185))
    # Thân
    body_top = size//6 + head_r*2 + 2
    d.ellipse((cx - head_r*2, body_top, cx + head_r*2, size - 4), fill=(160, 160, 185))
    return img

def DrawAdminList(owner_id, owner_name, admins, out_path, client):
    """Vẽ ảnh admin list theo phong cách mới"""
    W, H = 1600, 900
    PAD = 64

    # Tạo nền
    img = GradientBackground(W, H)
    BlobsEffect(img)
    NoiseEffect(img)

    # Card chính
    GlassEffect(img, (PAD, PAD, W - PAD, H - PAD), radius=40, alpha=glassFill, blur=26, aa=4)

    d = ImageDraw.Draw(img)

    # ── PHẦN OWNER (bên trái) ────────────────────────────────────────────
    OC_L = PAD + 20
    OC_T = PAD + 20
    OC_R = 520
    OC_B = H - PAD - 20
    OC_W = OC_R - OC_L

    # Card owner
    GlassEffect(img, (OC_L, OC_T, OC_R, OC_B), radius=30, alpha=(255, 255, 255, 22), blur=18)

    # Avatar owner
    AV_SIZE = 280
    av_x = OC_L + (OC_W - AV_SIZE) // 2
    av_y = OC_T + 45

    try:
        av_url = get_avatar_url(client, owner_id)
        av_raw = LoadImage(av_url, (AV_SIZE, AV_SIZE))
        av_img = CircleCrop(av_raw, AV_SIZE)
    except:
        av_img = PlaceholderAvatar(AV_SIZE)

    img.paste(av_img, (av_x, av_y), av_img)

    # Tên owner
    name_font = FontLib.Load("Dela-gothic-one.ttf", 36)
    name_cy = av_y + AV_SIZE + 35
    d.text((OC_L + OC_W // 2, name_cy), owner_name, font=name_font, fill=white, anchor="mt")

    # UID owner
    uid_font = FontLib.Load("Darley-sans.otf", 20)
    uid_cy = name_cy + 52
    d.text((OC_L + OC_W // 2, uid_cy), str(owner_id), font=uid_font, fill=dimgray, anchor="mt")

    # Badge "Admin Manager"
    BDG_W, BDG_H = 230, 50
    bdg_x = OC_L + (OC_W - BDG_W) // 2
    bdg_y = OC_B - 80
    d.rounded_rectangle((bdg_x, bdg_y, bdg_x + BDG_W, bdg_y + BDG_H), radius=25, fill=(40, 42, 60, 230))
    badge_font = FontLib.Load("Milker-Bold.otf", 22)
    d.text((bdg_x + BDG_W // 2, bdg_y + BDG_H // 2), "Admin Manager", font=badge_font, fill=(220, 220, 235), anchor="mm")

    # ── DANH SÁCH ADMIN (bên phải) ──────────────────────────────────────
    LST_X = OC_R + 35
    LST_Y = OC_T
    LST_W = W - PAD - 20 - LST_X

    ROW_H = 88
    ROW_PAD = 14
    AVS = 54

    admin_list = sorted(admins)
    max_rows = (OC_B - LST_Y) // (ROW_H + ROW_PAD)

    row_font_name = FontLib.Load("Dela-gothic-one.ttf", 26)
    row_font_role = FontLib.Load("Darley-sans.otf", 20)
    row_font_num = FontLib.Load("Dela-gothic-one.ttf", 24)

    for i, uid in enumerate(admin_list[:max_rows], 1):
        ry = LST_Y + (i - 1) * (ROW_H + ROW_PAD)

        # Row card
        GlassEffect(img, (LST_X, ry, LST_X + LST_W, ry + ROW_H), radius=20, alpha=(255, 255, 255, 18), blur=12)

        # Avatar nhỏ
        avs_x = LST_X + 18
        avs_y = ry + (ROW_H - AVS) // 2
        try:
            av_url2 = get_avatar_url(client, uid)
            av_raw2 = LoadImage(av_url2, (AVS, AVS))
            avs_img = CircleCrop(av_raw2, AVS)
        except:
            avs_img = PlaceholderAvatar(AVS)
        img.paste(avs_img, (avs_x, avs_y), avs_img)

        # Tên admin
        tx = avs_x + AVS + 18
        try:
            name = get_name(client, uid)
        except:
            name = str(uid)
        if len(name) > 22:
            name = name[:20] + "…"
        d.text((tx, ry + 16), name, font=row_font_name, fill=white)
        d.text((tx, ry + 50), "High Admin", font=row_font_role, fill=dimgray)

        # Số thứ tự
        d.text((LST_X + LST_W - 30, ry + ROW_H // 2), str(i), font=row_font_num, fill=(140, 150, 220), anchor="mm")

    # Lưu ảnh
    img.save(out_path, "PNG", optimize=True, compress_level=6)
    return out_path

def handle_admin(message, message_object, thread_id, thread_type, author_id, client):
    if not is_owner(author_id):
        _reply_mention(client, message_object, thread_id, thread_type, author_id, "ERROR", ["Bạn không có quyền!"], "#DB342E")
        return

    parts = message.split()
    if len(parts) < 2:
        _reply_mention(client, message_object, thread_id, thread_type, author_id, "WARNING", [
            "admin list - Xem danh sách admin",
            "admin add @user - Thêm admin",
            "admin remove @user - Xóa admin"
        ], "#F7B503")
        return

    cmd = parts[1].lower()
    admins = get_admins()
    owner = get_owner()
    owner_name = get_name(client, owner)

    if cmd == "list":
        out_path = os.path.join(CACHE_DIR, f"admin_list_{int(time.time())}.png")
        DrawAdminList(owner, owner_name, admins, out_path, client)
        
        with Image.open(out_path) as im:
            w, h = im.size
        
        client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type, 
                              message=Message(text=""), width=w, height=h)
        try:
            os.remove(out_path)
        except:
            pass
        return

    elif cmd == "add":
        uid = None
        if message_object.mentions:
            uid = message_object.mentions[0]["uid"]
        elif len(parts) > 2 and parts[2].isdigit():
            uid = parts[2]
        if not uid:
            _reply_mention(client, message_object, thread_id, thread_type, author_id, "WARNING", ["admin add @user"], "#F7B503")
            return
        if uid in admins:
            _reply_mention(client, message_object, thread_id, thread_type, author_id, "ERROR", ["Người dùng đã là admin!"], "#DB342E")
            return
        if uid == owner:
            _reply_mention(client, message_object, thread_id, thread_type, author_id, "ERROR", ["Không thể thêm chủ sở hữu!"], "#DB342E")
            return
        admins.add(uid)
        save_admins(admins)
        name = get_name(client, uid)
        _send_mention(client, uid, thread_id, thread_type, "SUCCESS", [f"Đã thêm {name} làm admin!"], "#15A85F")
        _reply_mention(client, message_object, thread_id, thread_type, author_id, "SUCCESS", [f"Đã thêm {name} làm admin!"], "#15A85F")

    elif cmd in ("remove", "rm"):
        uid = None
        if message_object.mentions:
            uid = message_object.mentions[0]["uid"]
        elif len(parts) > 2 and parts[2].isdigit():
            uid = parts[2]
        if not uid:
            _reply_mention(client, message_object, thread_id, thread_type, author_id, "WARNING", ["admin remove @user"], "#F7B503")
            return
        if uid not in admins:
            _reply_mention(client, message_object, thread_id, thread_type, author_id, "ERROR", ["Người dùng không phải admin!"], "#DB342E")
            return
        admins.remove(uid)
        save_admins(admins)
        name = get_name(client, uid)
        _send_mention(client, uid, thread_id, thread_type, "SUCCESS", [f"Đã xóa {name} khỏi admin!"], "#15A85F")
        _reply_mention(client, message_object, thread_id, thread_type, author_id, "SUCCESS", [f"Đã xóa {name} khỏi admin!"], "#15A85F")

    else:
        _reply_mention(client, message_object, thread_id, thread_type, author_id, "WARNING", ["admin list / add / remove"], "#F7B503")

def Kryzis():
    return {"admin": handle_admin}