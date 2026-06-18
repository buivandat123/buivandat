# -*- coding: utf-8 -*-
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_admin
import re
import time

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Tạo nhóm mới",
    'power': "Admin"
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

def create_group_direct(client, name, desc, members):
    try:
        member_types = [-1 for _ in members]
        params_data = {
            "clientId": str(int(time.time() * 1000)),
            "gname": name,
            "gdesc": desc,
            "members": members,
            "memberTypes": member_types,
            "nameChanged": 1 if name else 0,
            "createLink": 1,
            "clientLang": "vi",
            "imei": client._imei,
            "zsource": 601
        }
        params = {
            "zpw_ver": 645,
            "zpw_type": 30,
            "params": client._encode(params_data)
        }
        response = client._get("https://tt-group-wpa.chat.zalo.me/api/group/create/v2", params=params)
        data = response.json()
        if data.get("error_code") == 0:
            decoded = client._decode(data.get("data"))
            if decoded and decoded.get("data"):
                return decoded.get("data")
        return None
    except:
        return None

def get_group_link(client, group_id):
    try:
        params_data = {"grid": str(group_id)}
        params = {
            "zpw_ver": 650,
            "zpw_type": 30,
            "params": client._encode(params_data)
        }
        response = client._get("https://tt-group-wpa.chat.zalo.me/api/group/link/new", params=params)
        data = response.json()
        if data.get("error_code") == 0:
            decoded = client._decode(data.get("data"))
            if decoded and decoded.get("data") and decoded["data"].get("link"):
                return decoded["data"]["link"]
        return None
    except:
        return None

def handle_creategroup(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        msg = "ERROR\n    Bạn không có quyền!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return

    parts = message.split()
    
    if len(parts) < 2:
        msg = f"WARNING\n    {PREFIX}creategroup <tên nhóm>\n    {PREFIX}creategroup <số lượng> <tên>"
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)
        return
    
    if len(parts) >= 2 and parts[1].isdigit():
        count = int(parts[1])
        if count > 50:
            msg = "ERROR\n    Chỉ có thể tạo tối đa 50 nhóm!"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
            return
        name = parts[2] if len(parts) > 2 else "Group"
        
        success = 0
        for i in range(1, count + 1):
            group_name = f"{name} {i}"
            result = create_group_direct(client, group_name, "", [])
            if result:
                success += 1
            time.sleep(2)
        
        msg = f"SUCCESS\n    Đã tạo {success}/{count} nhóm!"
        client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
        return
    
    args = message.split(maxsplit=1)[1].strip()
    splitted = [x.strip() for x in args.split('|')]
    group_name = splitted[0]
    group_desc = splitted[1] if len(splitted) > 1 else ""
    members = [m for m in re.split(r'[,\s]+', splitted[2]) if m.isdigit()] if len(splitted) > 2 else []

    try:
        result = create_group_direct(client, group_name, group_desc, members)
        if result:
            group_id = result.get('groupId') or result.get('grid')
            if group_id:
                time.sleep(1)
                link = get_group_link(client, group_id)
                link_text = f"\n    Link: {link}" if link else ""
                msg = f"SUCCESS\n    Đã tạo nhóm: {group_name}\n    ID: {group_id}{link_text}"
                client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
            else:
                msg = "ERROR\n    Tạo nhóm thất bại!"
                client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        else:
            msg = "ERROR\n    Tạo nhóm thất bại!"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
    except Exception as e:
        msg = f"ERROR\n    {str(e)[:50]}"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)

def LIGHT():
    return {'creategroup': handle_creategroup}