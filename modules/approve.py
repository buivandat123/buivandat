# modules/approve.py
# -*- coding: utf-8 -*-
import time
import threading
import json
import os
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tự động duyệt thành viên vào nhóm",
    "power": "Admin"
}

# ============================================================
# STYLE (giống block.py)
# ============================================================

def _sty(text, color):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _sty_mention(text, tag_len, color):
    header_start = tag_len + 1
    header_end = text.find("\n", header_start)
    if header_end == -1:
        header_end = len(text)
    header_len = header_end - header_start + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False),
        MessageStyle(offset=header_start, length=header_len, style="color", color=color, auto_format=False),
        MessageStyle(offset=header_start, length=header_len, style="bold", auto_format=False),
    ])

def sty_ok(t):   return _sty(t, "#15A85F")
def sty_warn(t): return _sty(t, "#F7B503")
def sty_err(t):  return _sty(t, "#DB342E")
def sty_info(t): return _sty(t, "#00BFFF")

def _name(client, uid):
    try:
        p = client.fetchUserInfo(uid).changed_profiles.get(str(uid), {})
        return p.get("displayName", str(uid))
    except:
        return str(uid)

def _mention_msg(client, uid, header, lines, color):
    name = _name(client, uid)
    tag = f"@{name}"
    body = "\n".join(f"    {l}" for l in lines)
    text = f"{tag}\n{header}\n{body}"
    info = json.dumps([{"pos": 0, "uid": str(uid), "len": len(tag)}])
    style = _sty_mention(text, len(tag), color)
    return Message(text=text, mention=info, style=style)

def _reply(client, msg_obj, tid, ttype, text, sty_fn):
    client.replyMessage(Message(text=text, style=sty_fn(text)), msg_obj, tid, ttype)

def _mention_send(client, uid, tid, ttype, header, lines, color):
    msg = _mention_msg(client, uid, header, lines, color)
    client.sendMentionMessage(msg, tid)

# ============================================================
# CONFIG
# ============================================================

def get_settings_file(client):
    return f"data/services_{client.uid}.json"

def read_services(client):
    try:
        if os.path.exists(get_settings_file(client)):
            with open(get_settings_file(client), 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def write_services(client, data):
    try:
        os.makedirs("data", exist_ok=True)
        with open(get_settings_file(client), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def get_group_name(client, group_id):
    try:
        info = client.fetchGroupInfo(group_id)
        if hasattr(info, "gridInfoMap") and info.gridInfoMap:
            return info.gridInfoMap.get(str(group_id), {}).get("name", "Unknown")
    except:
        pass
    return "Unknown"

# ============================================================
# AUTO APPROVE LOOP
# ============================================================

def auto_approve_loop(client):
    def loop():
        while True:
            try:
                settings = read_services(client)
                groups = settings.get("approveGroup", [])
                for group_id in groups:
                    try:
                        pending = client.viewGroupPending(group_id)
                        if pending and hasattr(pending, 'users') and pending.users:
                            for user in pending.users:
                                try:
                                    client.handleGroupPending(user.uid, group_id, True)
                                    time.sleep(0.5)
                                except:
                                    pass
                    except:
                        pass
            except:
                pass
            time.sleep(3)
    threading.Thread(target=loop, daemon=True).start()

# ============================================================
# HANDLER
# ============================================================

def handle_approve(message, message_object, thread_id, thread_type, author_id, client):
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "ERROR\n    Bạn không có quyền!", sty_err)
        return

    parts = message.strip().split()
    settings = read_services(client)
    approve = settings.setdefault("approveGroup", [])
    enabled = thread_id in approve

    if len(parts) < 2:
        enabled = not enabled
    else:
        action = parts[1].lower()
        if action == "on":
            enabled = True
        elif action == "off":
            enabled = False
        else:
            _reply(client, message_object, thread_id, thread_type, 
                   f"WARNING\n    {parts[0]} on/off", sty_warn)
            return

    if enabled and thread_id not in approve:
        approve.append(thread_id)
        if not hasattr(client, '_approve_started'):
            client._approve_started = True
            auto_approve_loop(client)

    if not enabled and thread_id in approve:
        approve.remove(thread_id)

    write_services(client, settings)

    group_name = get_group_name(client, thread_id)
    status = "✅ ĐÃ BẬT" if enabled else "❌ ĐÃ TẮT"

    _mention_send(client, author_id, thread_id, thread_type, 
                  "SUCCESS" if enabled else "WARNING",
                  [f"👥 {group_name}", f"📊 {status}"],
                  "#15A85F" if enabled else "#F7B503")

# ============================================================
# LOAD
# ============================================================

def Kryzis():
    return {"approve": handle_approve}