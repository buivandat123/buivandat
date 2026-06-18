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

des = {"version":"1.0.0","credits":"kryzis X TXA","description":"Quản lý bạn bè","power":"Admin"}

def handle_friends(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Bạn không có quyền!",sty_err); return

    parts=message.split()
    action=parts[1].lower() if len(parts)>1 else ""
    if not action:
        _reply(client,message_object,thread_id,thread_type,
               f"WARNING\n    {PREFIX}friends list / count / search <tên>",sty_warn); return

    try:
        fd=client.fetchAllFriends()
        fl=(fd["data"] if isinstance(fd,dict) and "data" in fd
            else fd if isinstance(fd,list) else [])
        if not fl:
            _reply(client,message_object,thread_id,thread_type,"WARNING\n    Không có bạn bè!",sty_warn); return

        if action=="count":
            _mention_send(client, author_id, thread_id, thread_type, "BẠN BÈ 👥",
                          [f"👥 Tổng bạn bè: {len(fl)}"], "#15A85F")

        elif action=="list":
            names=[f"  {i}. {(f.displayName if hasattr(f,'displayName') else str(f))}"
                   for i,f in enumerate(fl[:30],1)]
            extra=[f"  ... và {len(fl)-30} người khác"] if len(fl)>30 else []
            _mention_send(client, author_id, thread_id, thread_type, "DANH SÁCH BẠN BÈ 👥",
                          names+extra, "#15A85F")

        elif action=="search" and len(parts)>2:
            kw=parts[2].lower()
            found=[f"  • {(f.displayName if hasattr(f,'displayName') else str(f))}"
                   for f in fl if kw in (f.displayName if hasattr(f,'displayName') else "").lower()]
            if found:
                _mention_send(client, author_id, thread_id, thread_type, f"KẾT QUẢ '{parts[2]}'", found[:30], "#15A85F")
            else:
                _reply(client,message_object,thread_id,thread_type,
                       f"WARNING\n    Không tìm thấy '{parts[2]}'!",sty_warn)
        else:
            _reply(client,message_object,thread_id,thread_type,
                   f"WARNING\n    {PREFIX}friends list / count / search <tên>",sty_warn)
    except Exception as e:
        _reply(client,message_object,thread_id,thread_type,f"ERROR\n    {str(e)[:60]}",sty_err)

def LIGHT(): return {"friends": handle_friends}
