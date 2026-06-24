# -*- coding: utf-8 -*-
import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

def _sty(text, color):
    """Style cho tin nhắn thường (không có @tag): dòng đầu màu + bold."""
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font",  size="9",   auto_format=False),
        MessageStyle(offset=0, length=h,          style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h,          style="bold",              auto_format=False),
    ])

def _sty_mention(text, tag_len, color):
    """
    Style cho tin nhắn có @tag ở đầu:
      - @Tên   → không màu, không bold (plain)
      - HEADER → màu + bold  (offset bắt đầu sau tag + newline)
      - nội dung bên dưới → font 9
    """
    # tag_len = len("@Tên"), +1 cho ký tự newline
    header_start = tag_len + 1
    header_end   = text.find("\n", header_start)
    if header_end == -1:
        header_end = len(text)
    header_len = header_end - header_start + 1  # +1 cho newline sau header

    return MultiMsgStyle([
        # Toàn bộ: font 9
        MessageStyle(offset=0,            length=len(text),   style="font",  size="9",   auto_format=False),
        # Header (SUCCESS/ERROR/WARNING): màu
        MessageStyle(offset=header_start, length=header_len,  style="color", color=color, auto_format=False),
        # Header: bold
        MessageStyle(offset=header_start, length=header_len,  style="bold",              auto_format=False),
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
    """
    Tạo tin nhắn dạng:
        @Tên          ← plain, không màu
        HEADER        ← màu + bold
            line 1
            line 2
    """
    name = _name(client, uid)
    tag  = f"@{name}"
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
from asset.admin_check import is_admin

des = {"version":"1.0.0","credits":"kryzis X TXA","description":"Bỏ chặn người dùng","power":"Admin"}

def handle_unblock(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Bạn không có quyền!",sty_err); return

    uid=None
    if thread_type==ThreadType.USER: uid=str(thread_id)
    elif message_object.mentions:    uid=message_object.mentions[0]["uid"]
    else:
        parts=message.split()
        if len(parts)>1 and parts[1].isdigit(): uid=parts[1]
    if not uid:
        _reply(client,message_object,thread_id,thread_type,
               f"WARNING\n    {PREFIX}unblock @user",sty_warn); return

    try:
        client.unblockUser(uid)
        _mention_send(client, uid, thread_id, thread_type, "SUCCESS",
                      ["✅ Đã được bỏ chặn!"], "#15A85F")
    except Exception as e:
        _reply(client,message_object,thread_id,thread_type,f"ERROR\n    {str(e)[:60]}",sty_err)

def Kryzis(): return {"unblock": handle_unblock}
