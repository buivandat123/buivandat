# modules/admin.py
# -*- coding: utf-8 -*-
import json
import os
import time
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from modules.canvas import *

des = {"version": "1.0.0", "credits": "kryzis X TXA", "description": "Quản lý admin bot", "power": "Owner"}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETING_FILE = os.path.join(BASE_DIR, "asset", "seting.json")
CACHE_DIR = "/sdcard/download/kryzis/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

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

def get_avatar(client, uid):
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

def DrawAdminList(owner_id, owner_name, admins, out_path, client):
    img = CreateBackground(W, H)
    card = (PAD, PAD, W - PAD, H - PAD)
    Glass(img, card, radius=40)
    d = ImageDraw.Draw(img)
    
    # Bên trái: avatar chủ
    LeftW = 300
    Gap = 25
    Inner = 22
    Lx1 = PAD + Inner
    Ly1 = PAD + Inner
    Lx2 = Lx1 + LeftW
    Ly2 = H - PAD - Inner
    Glass(img, (Lx1, Ly1, Lx2, Ly2), radius=35)
    
    avatar_size = 150
    avatar_url = get_avatar(client, owner_id)
    avatar = LoadImage(avatar_url, (500, 500))
    avatar = CircleCrop(avatar, avatar_size)
    avatar_x = Lx1 + (LeftW - avatar_size) // 2
    avatar_y = Ly1 + 30
    img.paste(avatar, (avatar_x, avatar_y), avatar)
    
    name_font = Font(28, bold=True)
    name_fit = FitText(d, owner_name, name_font, LeftW - 30)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 15), name_fit, font=name_font, fill=TextTitle, anchor="mm")
    role_font = Font(20)
    d.text((Lx1 + LeftW // 2, avatar_y + avatar_size + 45), "OWNER", font=role_font, fill=(255, 80, 80), anchor="mm")
    
    # Bên phải: danh sách admin
    Rx1 = Lx2 + Gap
    Ry1 = Ly1
    Rx2 = W - PAD - Inner
    title_font = Font(36, bold=True)
    d.text(((Rx1 + Rx2) // 2, Ry1 + 25), "ADMIN LIST", font=title_font, fill=TextTitle, anchor="mm")
    
    if not admins:
        d.text(((Rx1 + Rx2) // 2, Ry1 + 100), "Không có admin phụ", font=Font(26), fill=TextDim, anchor="mm")
    else:
        start_y = Ry1 + 80
        row_h = 45
        max_rows = 10
        
        for i, uid in enumerate(sorted(admins), 1):
            if i > max_rows:
                break
            y = start_y + (i - 1) * row_h
            if y > Ry1 + 450:
                break
            
            # Lấy tên thật
            try:
                name = get_name(client, uid)
            except:
                name = str(uid)
            
            # Nếu tên quá dài, cắt ngắn
            if len(name) > 25:
                name = name[:22] + "..."
            
            d.text((Rx1 + 25, y), f"{i}.", font=Font(24, bold=True), fill=TextDim)
            d.text((Rx1 + 55, y), name, font=Font(24), fill=TextSub)
    
    # Footer
    total = len(admins) + 1
    footer_font = Font(22)
    d.text((W // 2, H - PAD - 20), f"Tổng số: {total} admin", font=footer_font, fill=TextDim, anchor="mm")
    
    # Lưu ảnh nhanh
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

def LIGHT():
    return {"admin": handle_admin}
