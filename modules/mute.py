# modules/mute.py
# -*- coding: utf-8 -*-
import time
import json
import os
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Cấm nói trong nhóm",
    "power": "ADMIN"
}

MUTE_FILE = "modules/cache/muted_users.json"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def load_muted():
    if os.path.exists(MUTE_FILE):
        try:
            with open(MUTE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_muted(data):
    os.makedirs(os.path.dirname(MUTE_FILE), exist_ok=True)
    with open(MUTE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_muted(uid, tid):
    data = load_muted()
    key = f"{uid}_{tid}"
    info = data.get(key)
    if not info:
        return False
    until = info.get('until')
    if until and time.time() > until:
        del data[key]
        save_muted(data)
        return False
    return True

def handle_mute(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    if thread_type != ThreadType.GROUP:
        _reply(client, message_object, thread_id, thread_type, "❌ Chỉ dùng trong nhóm")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, 
               f"{PREFIX}mute @user <phút> <lý do>\n{PREFIX}mute unmute @user\n{PREFIX}mute list")
        return
    
    cmd = parts[1].lower()
    
    uid = None
    if message_object.mentions:
        uid = message_object.mentions[0]['uid']
    elif hasattr(message_object, 'replyId') and message_object.replyId:
        try:
            replied = client.fetchMessage(thread_id, message_object.replyId)
            if replied:
                uid = replied.authorId
        except:
            pass
    
    if cmd == 'list':
        data = load_muted()
        lines = ["🔇 MUTE LIST"]
        for k, v in data.items():
            if k.endswith(f"_{thread_id}"):
                u = k.split('_')[0]
                until = v.get('until')
                if until:
                    remain = int(until - time.time())
                    t_str = f"{remain//60}p{remain%60}s"
                else:
                    t_str = "Vĩnh viễn"
                lines.append(f"• {u} | {t_str} | {v.get('reason', '?')}")
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines) if len(lines)>1 else "📭 Trống")
        return
    
    if cmd == 'unmute':
        if not uid:
            _reply(client, message_object, thread_id, thread_type, "Tag hoặc reply người cần unmute")
            return
        key = f"{uid}_{thread_id}"
        data = load_muted()
        if key in data:
            del data[key]
            save_muted(data)
            _reply(client, message_object, thread_id, thread_type, "✅ Đã bỏ mute")
        else:
            _reply(client, message_object, thread_id, thread_type, "❌ Không bị mute")
        return
    
    if not uid:
        _reply(client, message_object, thread_id, thread_type, "Tag hoặc reply người cần mute")
        return
    
    try:
        minutes = int(parts[2])
    except:
        _reply(client, message_object, thread_id, thread_type, "❌ Số phút không hợp lệ")
        return
    
    reason = " ".join(parts[3:]) if len(parts) > 3 else "Không có lý do"
    
    data = load_muted()
    key = f"{uid}_{thread_id}"
    data[key] = {
        'until': time.time() + minutes * 60 if minutes > 0 else None,
        'reason': reason,
        'by': author_id
    }
    save_muted(data)
    
    _reply(client, message_object, thread_id, thread_type, f"🔇 Đã mute {minutes if minutes>0 else 'vĩnh viễn'} phút\n📝 {reason}")

def LIGHT():
    return {"mute": handle_mute}