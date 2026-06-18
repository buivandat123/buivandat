# -*- coding: utf-8 -*-
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_admin
from datetime import datetime

des = {
    'version': "1.0.1",
    'credits': "kryzis X TXA",
    'description': "Nâng cấp nhóm lên Community (hỗ trợ lệnh upcommunity / upcom)",
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

def handle_upcommunity(message, message_object, thread_id, thread_type, author_id, client):

    if thread_type != ThreadType.GROUP:
        client.replyMessage(
            Message(text="WARNING\n    Có Phải Box Đâu Mà Đòi Nâng?", style=warning_style()),
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
        try:
            group_info = client.fetchGroupInfo(thread_id)
            group_data = group_info.gridInfoMap.get(str(thread_id), {})
            total_mem = group_data.get("totalMember", "Không rõ")
            created_time = group_data.get("createdTime", 0)
            created_date = datetime.fromtimestamp(int(created_time)).strftime('%d/%m/%Y %H:%M:%S') if created_time else "Không rõ"
        except:
            total_mem = "Không rõ"
            created_date = "Không rõ"

        result = client.upgradeComunity(thread_id)
        print(f"[upcommunity] result: {result}")

        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        # Check error_code bên trong result (Zalo hay trả về error trong decoded)
        inner_code = 0
        inner_msg = ""
        if isinstance(result, dict):
            inner_code = result.get("error_code", 0)
            inner_msg = result.get("error_message", "")
            data = result.get("data", {})
            if isinstance(data, dict):
                inner_msg = data.get("error_message_localize", inner_msg)

        if inner_code == 0:
            success_msg = f"""SUCCESS
    Nâng Cấp Community Thành Công!
    ID Group: {thread_id}
    Total Member: {total_mem}
    Time: {current_time}"""
            client.replyMessage(Message(text=success_msg, style=success_style()), message_object, thread_id, thread_type)
        else:
            _map_error(inner_code, inner_msg, client, message_object, thread_id, thread_type)

    except Exception as e:
        print(f"[upcommunity] exception: {e}")
        err = str(e).lower()
        err_raw = str(e)
        if "community" in err or "already" in err or "đã" in err or "#185" in err_raw:
            msg = "WARNING\n    Box Comunity Rồi Up Con Cặc"
        elif "#-1403" in err_raw or "permission" in err or "admin" in err:
            msg = "WARNING\n    Có Key Vàng Đâu Mà Nâng"
        elif "#-1008" in err_raw or "key" in err:
            msg = "WARNING\n    Lên Web Zbusiness Nâng Business Đi"
        else:
            msg = f"WARNING\n    Lỗi: {err_raw}"
        client.replyMessage(Message(text=msg, style=warning_style()), message_object, thread_id, thread_type)

def _map_error(code, msg, client, message_object, thread_id, thread_type):
    if code == 185 or "cộng đồng" in msg.lower() or "community" in msg.lower():
        text = "WARNING\n    Box Comunity Rồi Up Con Cặc"
    elif code in [-1403, -1]:
        text = "WARNING\n    Có Key Vàng Đâu Mà Nâng"
    elif code in [-1008, -2]:
        text = "WARNING\n    Lên Web Zbusiness Nâng Business Đi"
    else:
        text = f"WARNING\n    Lỗi #{code}: {msg}"
    client.replyMessage(Message(text=text, style=warning_style()), message_object, thread_id, thread_type)

def LIGHT():
    return {
        'upcommunity': handle_upcommunity,
        'upcom': handle_upcommunity
    }
