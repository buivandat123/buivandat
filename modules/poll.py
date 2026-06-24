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

des = {"version":"1.0.0","credits":"kryzis X TXA","description":"Tạo/kết thúc bình chọn","power":"Admin"}

def handle_poll(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Bạn không có quyền!",sty_err); return
    if thread_type!=ThreadType.GROUP:
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Chỉ dùng trong nhóm!",sty_err); return

    parts=message.split(maxsplit=1)
    if len(parts)<2:
        _reply(client,message_object,thread_id,thread_type,
               f"WARNING\n    {PREFIX}poll <câu hỏi> | <lựa chọn 1> | <lựa chọn 2>",sty_warn); return

    sp=[x.strip() for x in parts[1].split("|")]
    if len(sp)<3:
        _reply(client,message_object,thread_id,thread_type,
               f"WARNING\n    Cần ít nhất 2 lựa chọn!\n    {PREFIX}poll Q | A | B",sty_warn); return

    question,options=sp[0],sp[1:]
    try:
        r=client.createPoll(question=question,options=options,groupId=thread_id,
                            expiredTime=0,pinAct=False,multiChoices=True,
                            allowAddNewOption=False,hideVotePreview=False,isAnonymous=False)
        pid=(getattr(r,"poll_id",None) or getattr(r,"pollId",None)
             or (r.get("poll_id") or r.get("pollId") if isinstance(r,dict) else None))
        lines=[f"📊 Câu hỏi: {question}",
               f"🗳️  {len(options)} lựa chọn",
               *(f"  {i+1}. {o}" for i,o in enumerate(options)),
               f"🆔 Poll ID: {pid}" if pid else ""]
        _mention_send(client, author_id, thread_id, thread_type, "POLL TẠO THÀNH CÔNG",
                      [l for l in lines if l], "#15A85F")
    except Exception as e:
        _reply(client,message_object,thread_id,thread_type,f"ERROR\n    {str(e)[:60]}",sty_err)

def handle_endpoll(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Bạn không có quyền!",sty_err); return
    parts=message.split()
    if len(parts)<2 or not parts[1].isdigit():
        _reply(client,message_object,thread_id,thread_type,
               f"WARNING\n    {PREFIX}endpoll <poll_id>",sty_warn); return
    try:
        client.lockPoll(parts[1])
        _mention_send(client, author_id, thread_id, thread_type, "SUCCESS",
                      [f"✅ Đã kết thúc poll #{parts[1]}!"], "#15A85F")
    except Exception as e:
        _reply(client,message_object,thread_id,thread_type,f"ERROR\n    {str(e)[:60]}",sty_err)

def Kryzis(): return {"poll": handle_poll, "endpoll": handle_endpoll}
