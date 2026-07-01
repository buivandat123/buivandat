# -*- coding: utf-8 -*-
import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

def _sty(text, color):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=10000, style="font", size="9", auto_format=False),
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
        MessageStyle(offset=0, length=10000, style="font", size="9", auto_format=False),
        MessageStyle(offset=header_start, length=header_len, style="color", color=color, auto_format=False),
        MessageStyle(offset=header_start, length=header_len, style="bold", auto_format=False),
    ])

def sty_ok(t): return _sty(t, "#15A85F")
def sty_warn(t): return _sty(t, "#F7B503")
def sty_err(t): return _sty(t, "#DB342E")
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

from asset.config import PREFIX
from datetime import datetime

des = {"version": "1.0.0", "credits": "kryzis X TXA", "description": "Xem thông tin nhóm", "power": "Member"}

def _ts(ts):
    try:
        return datetime.fromtimestamp(int(ts)/1000).strftime("%d/%m/%Y %H:%M")
    except:
        return "?"

def handle_grif(message, message_object, thread_id, thread_type, author_id, client):
    if thread_type != ThreadType.GROUP:
        _reply(client, message_object, thread_id, thread_type, "ERROR\n    Chỉ dùng trong nhóm!", sty_err)
        return

    gid = thread_id
    parts = message.split()
    if len(parts) > 1 and parts[1].startswith("https://zalo.me/g/"):
        try:
            info = client.getIDsGroup(parts[1])
            if info and "groupId" in info:
                gid = info["groupId"]
        except:
            pass

    try:
        gd = client.fetchGroupInfo(gid).gridInfoMap.get(str(gid), {})
        if not gd:
            _reply(client, message_object, thread_id, thread_type, "WARNING\n    Không tìm thấy nhóm!", sty_warn)
            return

        st = gd.get("setting", {})
        adm = gd.get("adminIds", [])
        creator_id = gd.get("creatorId", "")
        
        creator_name = _name(client, creator_id) if creator_id else "Không rõ"
        admin_count = len([uid for uid in adm if str(uid) != str(creator_id)])
        
        group_type = "Community" if gd.get("type") == 2 else "Normal"
        lock_send = "Có" if st.get("lockSendMsg") == 1 else "Không"
        join_appr = "Có" if st.get("joinAppr") == 1 else "Không"
        block_name = "Có" if st.get("blockName") == 1 else "Không"
        sign_admin = "Có" if st.get("signAdminMsg") == 1 else "Không"
        add_member_only = "Có" if st.get("addMemberOnly") == 1 else "Không"
        lock_create_post = "Có" if st.get("lockCreatePost") == 1 else "Không"
        lock_create_poll = "Có" if st.get("lockCreatePoll") == 1 else "Không"
        set_topic_only = "Có" if st.get("setTopicOnly") == 1 else "Không"
        enable_msg_history = "Có" if st.get("enableMsgHistory") == 1 else "Không"
        
        lines = [
            f"Tên: {gd.get('name', 'Không rõ')}",
            f"ID: {gid}",
            f"Loại: {group_type}",
            f"Thành viên: {gd.get('totalMember', '0')}",
            f"Tạo lúc: {_ts(gd.get('createdTime', 0))}",
            f"Key vàng: {creator_name}",
            f"Phó nhóm: {admin_count}",
            f"Link: {gd.get('link', 'Chưa có')}",
            "",
            "CÀI ĐẶT:",
            f"  Khóa chat: {lock_send}",
            f"  Duyệt thành viên: {join_appr}",
            f"  Khóa đổi tên/ảnh: {block_name}",
            f"  Đánh dấu tin nhắn admin: {sign_admin}",
            f"  Chỉ admin thêm thành viên: {add_member_only}",
            f"  Khóa tạo ghi chú: {lock_create_post}",
            f"  Khóa tạo bình chọn: {lock_create_poll}",
            f"  Chỉ admin ghim: {set_topic_only}",
            f"  Lưu tin nhắn cũ: {enable_msg_history}",
        ]
        _mention_send(client, author_id, thread_id, thread_type, "GROUP INFO", lines, "#15A85F")
        
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, f"ERROR\n    {str(e)[:60]}", sty_err)

def Kryzis():
    return {"grif": handle_grif, "ifgr": handle_grif}