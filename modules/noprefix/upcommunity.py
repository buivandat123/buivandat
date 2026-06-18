# -*- coding: utf-8 -*-
import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from datetime import datetime

des = {
    'version': "1.2.0",
    'credits': "kryzis X TXA",
    'description': "Nang cap nhom len Community - Khong can prefix",
    'power': "Admin"
}

def is_admin(author_id):
    try:
        with open("asset/seting.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            owner = str(data.get("admin", ""))
            admins = [str(x) for x in data.get("adm", [])]
            return str(author_id) == owner or str(author_id) in admins
    except:
        return False

def warning_style():
    return MultiMsgStyle([
        MessageStyle(offset=0, length=7,      style="bold",                   auto_format=False),
        MessageStyle(offset=0, length=7,      style="color", color="#F7B503", auto_format=False),
        MessageStyle(offset=0, length=100000, style="font",  size="0",        auto_format=False)
    ])

def success_style():
    return MultiMsgStyle([
        MessageStyle(offset=0, length=11,     style="bold",                   auto_format=False),
        MessageStyle(offset=0, length=11,     style="color", color="#15A85F", auto_format=False),
        MessageStyle(offset=0, length=100000, style="font",  size="0",        auto_format=False)
    ])

def handle_upcomunity(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")

    if thread_type != ThreadType.GROUP:
        client.replyMessage(
            Message(text="WARNING\n    Co Phai Box Dau Ma Doi Nang?", style=warning_style()),
            message_object, thread_id, thread_type
        )
        return

    if not is_admin(author_id):
        client.replyMessage(
            Message(text="WARNING\n    May Co Quyen Dau Em?", style=warning_style()),
            message_object, thread_id, thread_type
        )
        return

    try:
        # Lay thong tin nhom truoc khi nang cap
        try:
            group_info = client.fetchGroupInfo(thread_id)
            group_data = group_info.gridInfoMap.get(str(thread_id), {})
            total_mem = group_data.get("totalMember", "Khong ro")
            group_name = group_data.get("name", "Khong ro")
        except:
            total_mem = "Khong ro"
            group_name = "Khong ro"

        # Gui thong bao dang xu ly
        client.replyMessage(
            Message(text="SUCCESS\n    ⏳ Dang tien hanh nang cap nhom len Community...\nVui long cho giay lat!", style=warning_style()),
            message_object, thread_id, thread_type
        )

        # Thuc hien nang cap
        result = client.upgradeComunity(thread_id)
        
        # In ket qua JSON ra console de debug
        print(f"[upcomunity] JSON result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        # Kiem tra ket qua tu API tra ve
        if isinstance(result, dict):
            # Lay cac gia tri quan trong
            error_code = result.get("error_code", 0)
            successfully = 1 if error_code == 0 else 0
            error_message = result.get("error_message", "")
            data = result.get("data", {})
            
            # Lay thong tin chi tiet tu data
            community_id = data.get("communityId", "") or data.get("gridId", "") or str(thread_id)
            community_name = data.get("communityName", "") or group_name
            member_count = data.get("memberCount", 0) or total_mem
            
            # Tao response JSON
            response = {
                "successfully": successfully,
                "error_code": error_code,
                "error_message": error_message,
                "data": {
                    "community_id": community_id,
                    "community_name": community_name,
                    "member_count": member_count,
                    "upgrade_time": current_time
                }
            }
            
            print(f"[upcomunity] Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
            
            if error_code == 0:
                # Thanh cong
                success_msg = f"""{json.dumps(response, indent=2, ensure_ascii=False)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 NANG CAP COMMUNITY THANH CONG!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📛 Ten nhom: {community_name}
🆔 ID Community: {community_id}
👥 So thanh vien: {member_count}
⏰ Thoi gian: {current_time}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Chuc mung nhom da tro thanh Community!"""
                client.replyMessage(Message(text=success_msg, style=success_style()), message_object, thread_id, thread_type)
            else:
                # That bai
                _map_error(error_code, error_message, client, message_object, thread_id, thread_type, response)
        else:
            # Neu result khong phai dict
            response = {
                "successfully": 0,
                "error_code": -1,
                "error_message": "Khong nhan duoc phan hoi tu API",
                "data": {}
            }
            client.replyMessage(
                Message(text=f"WARNING\n    Loi: {result}", style=warning_style()),
                message_object, thread_id, thread_type
            )

    except Exception as e:
        print(f"[upcomunity] exception: {e}")
        err_raw = str(e)
        response = {
            "successfully": 0,
            "error_code": -999,
            "error_message": err_raw[:200],
            "data": {}
        }
        if "community" in err_raw.lower() or "already" in err_raw.lower():
            msg = "WARNING\n    Box Community Roi Up Con Cac"
        elif "#-1403" in err_raw or "permission" in err_raw.lower():
            msg = "WARNING\n    Co Key Vang Dau Ma Nang"
        elif "#-1008" in err_raw:
            msg = "WARNING\n    Len Web Zbusiness Nang Business Di"
        else:
            msg = f"WARNING\n    Loi: {err_raw[:100]}"
        client.replyMessage(Message(text=msg, style=warning_style()), message_object, thread_id, thread_type)

def _map_error(code, msg, client, message_object, thread_id, thread_type, response=None):
    if response is None:
        response = {
            "successfully": 0,
            "error_code": code,
            "error_message": msg,
            "data": {}
        }
    
    print(f"[upcomunity] Error response: {json.dumps(response, indent=2, ensure_ascii=False)}")
    
    if code == 185 or "cong dong" in msg.lower() or "community" in msg.lower():
        text = "WARNING\n    Box Community Roi Up Con Cac"
    elif code in [-1403, -1]:
        text = "WARNING\n    Co Key Vang Dau Ma Nang"
    elif code in [-1008, -2]:
        text = "WARNING\n    Len Web Zbusiness Nang Business Di"
    else:
        text = f"WARNING\n    Loi #{code}: {msg[:100]}"
    
    client.replyMessage(Message(text=text, style=warning_style()), message_object, thread_id, thread_type)

def LIGHT():
    """Export cho noprefix"""
    return {
        "up cộng đồng": handle_upcomunity,
        "upgradecommunity": handle_upcomunity,
        "up community": handle_upcomunity,
        "nang cap community": handle_upcomunity,
        "len community": handle_upcomunity
    }