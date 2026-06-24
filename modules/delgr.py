# -*- coding: utf-8 -*-
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_admin

des = {
    'version': "1.0.0",
    'credits': "TXA",
    'description': "Giải tán nhóm hiện tại (Chỉ Admin bot và bot phải là Trưởng nhóm)",
    'power': "Admin"
}

def warning_style():
    return MultiMsgStyle([
        MessageStyle(offset=0, length=7,      style="bold",                   auto_format=False),
        MessageStyle(offset=0, length=7,      style="color", color="#F7B503", auto_format=False),
        MessageStyle(offset=0, length=100000, style="font",  size="0",        auto_format=False)
    ])

def success_style():
    return MultiMsgStyle([
        MessageStyle(offset=0, length=7,      style="bold",                   auto_format=False),
        MessageStyle(offset=0, length=7,      style="color", color="#15A85F", auto_format=False),
        MessageStyle(offset=0, length=100000, style="font",  size="0",        auto_format=False)
    ])

def handle_delgr(message, message_object, thread_id, thread_type, author_id, client):

    if thread_type != ThreadType.GROUP:
        client.replyMessage(
            Message(text="WARNING\n    Lệnh này chỉ dùng được trong Box nhóm!", style=warning_style()),
            message_object, thread_id, thread_type
        )
        return

    if not is_admin(author_id):
        client.replyMessage(
            Message(text="WARNING\n    Mày Có Quyền Đâu Em?", style=warning_style()),
            message_object, thread_id, thread_type
        )
        return

    try:
        # Thực thi giải tán nhóm
        result = client.disperseGroup(thread_id)
        print(f"[delgr] disperse result: {result}")
        
        # Thường giải tán nhóm thành công thì nhóm sẽ biến mất ngay lập tức
        # Gửi thông báo thành công (nếu kịp)
        success_msg = f"""SUCCESS
    Giải tán nhóm thành công!
    ID Group: {thread_id}"""
        client.replyMessage(Message(text=success_msg, style=success_style()), message_object, thread_id, thread_type)

    except Exception as e:
        print(f"[delgr] exception: {e}")
        err = str(e).lower()
        err_raw = str(e)
        if "permission" in err or "owner" in err or "-1403" in err_raw:
            msg = "WARNING\n    Có Phải Trưởng Nhóm Đâu Mà Đòi Giải Tán?"
        else:
            msg = f"WARNING\n    Lỗi giải tán nhóm: {err_raw}"
        client.replyMessage(Message(text=msg, style=warning_style()), message_object, thread_id, thread_type)

def Kryzis():
    return {'delgr': handle_delgr}
