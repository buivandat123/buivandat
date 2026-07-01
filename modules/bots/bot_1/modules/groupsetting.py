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

des = {"version":"1.0.0","credits":"kryzis X TXA","description":"Cài đặt nhóm","power":"Admin"}

CMDS = {
    "lockname":       ("blockName",    1,  "🔒 Đã khóa đổi tên & ảnh!"),
    "unlockname":     ("blockName",    0,  "🔓 Đã mở khóa đổi tên!"),
    "locksend_on":    ("lockSendMsg",  1,  "🔒 Đã khóa gửi tin nhắn!"),
    "locksend_off":   ("lockSendMsg",  0,  "🔓 Đã mở khóa gửi tin!"),
    "lockview_on":    ("lockViewMember",1, "🔒 Đã khóa xem thành viên!"),
    "lockview_off":   ("lockViewMember",0, "🔓 Đã mở khóa xem thành viên!"),
    "signmsg_on":     ("signAdminMsg", 1,  "✅ Đã bật ký hiệu tin admin!"),
    "signmsg_off":    ("signAdminMsg", 0,  "❌ Đã tắt ký hiệu tin admin!"),
    "addmemberonly_on":("addMemberOnly",1, "✅ Chỉ admin thêm thành viên!"),
    "addmemberonly_off":("addMemberOnly",0,"❌ Ai cũng thêm thành viên!"),
    "joinappr_on":    ("joinAppr",     1,  "✅ Bật duyệt thành viên mới!"),
    "joinappr_off":   ("joinAppr",     0,  "❌ Tắt duyệt thành viên!"),
}

def handle_groupsetting(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Bạn không có quyền!",sty_err); return
    if thread_type!=ThreadType.GROUP:
        _reply(client,message_object,thread_id,thread_type,"ERROR\n    Chỉ dùng trong nhóm!",sty_err); return

    parts=message.split()
    if len(parts)<2:
        lines=[f"  {PREFIX}{c.replace('_',' ')} " for c in CMDS]
        _mention_send(client, author_id, thread_id, thread_type, "CÀI ĐẶT NHÓM ⚙️", lines, "#F7B503"); return

    cmd=parts[1].lower()
    val=parts[2].lower() if len(parts)>2 else ""
    key=f"{cmd}_{val}" if val in ("on","off") else cmd

    if key in CMDS:
        kwarg, v, ok_text = CMDS[key]
        try:
            if cmd=="antiraid":
                client.changeGroupSetting(thread_id, defaultMode="anti-raid" if v==1 else "default")
            else:
                client.changeGroupSetting(thread_id, **{kwarg: v})
            _mention_send(client, author_id, thread_id, thread_type, "SUCCESS", [ok_text], "#15A85F")
        except Exception as e:
            _reply(client,message_object,thread_id,thread_type,f"ERROR\n    {str(e)[:60]}",sty_err)
    else:
        lines=[f"  {PREFIX}{c.replace('_',' ')} " for c in CMDS]
        _mention_send(client, author_id, thread_id, thread_type, "CÀI ĐẶT NHÓM ⚙️", lines, "#F7B503")

def Kryzis(): return {"groupsetting": handle_groupsetting}
