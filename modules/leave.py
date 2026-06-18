# modules/leave.py
# -*- coding: utf-8 -*-
import time
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Rời nhóm",
    "power": "ADMIN"
}

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def handle_leave(message, message_object, thread_id, thread_type, author_id, client):
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    _reply(client, message_object, thread_id, thread_type, "👋 Tạm biệt!")
    
    def leave():
        time.sleep(2)
        try:
            # Thử kick chính bot
            client.kickUser(client.uid, thread_id)
        except Exception as e:
            print(f"Kick error: {e}")
            try:
                # Thử leaveGroup
                client.leaveGroup(thread_id)
            except Exception as e2:
                print(f"Leave error: {e2}")
    
    threading.Thread(target=leave, daemon=True).start()

def LIGHT():
    return {"leave": handle_leave}