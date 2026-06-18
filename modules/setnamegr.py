# -*- coding: utf-8 -*-
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_admin

des = {
    'version': "1.0.0",
    'credits': "Light",
    'description': "Đổi tên nhóm",
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

def handle_setname(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        msg = "ERROR\n    Bạn không có quyền!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return

    if thread_type != ThreadType.GROUP:
        msg = "ERROR\n    Chỉ dùng trong nhóm!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return

    parts = message.split(maxsplit=1)
    if len(parts) < 2:
        msg = f"WARNING\n    {PREFIX}setnamegr <tên nhóm mới>"
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)
        return

    new_name = parts[1].strip()
    if not new_name:
        msg = f"WARNING\n    {PREFIX}setnamegr <tên nhóm mới>"
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)
        return

    try:
        result = client.changeGroupName(new_name, thread_id)
        msg = f"SUCCESS\n    Đã đổi tên nhóm thành: {new_name}"
        client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)

    except Exception as e:
        if "permission" in str(e).lower():
            msg = "ERROR\n    Bot không có quyền đổi tên!"
        else:
            msg = f"ERROR\n    {str(e)[:50]}"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)

def LIGHT():
    return {'setnamegr': handle_setname}