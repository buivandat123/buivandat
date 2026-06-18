# modules/eval.py
# -*- coding: utf-8 -*-
import io
import sys
import os
import traceback
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "2.0.0",
    "credits": "Kryzis",
    "description": "Thực thi code Python + chỉnh sửa file",
    "power": "Admin"
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

def handle_eval(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    from asset.admin_check import is_admin
    
    if not is_admin(author_id):
        _reply(client, message_object, thread_id, thread_type, "❌ Admin only")
        return
    
    code = message[len(PREFIX + "eval"):].strip()
    if not code:
        _reply(client, message_object, thread_id, thread_type, 
               f"📝 {PREFIX}eval <code>\n\n"
               f"📝 {PREFIX}eval --file <đường dẫn> <nội dung>\n"
               f"📝 {PREFIX}eval --read <đường dẫn>\n"
               f"📝 {PREFIX}eval --run <đường dẫn>\n\n"
               f"VD:\n"
               f"  {PREFIX}eval print('hello')\n"
               f"  {PREFIX}eval --file test.py print('hello')\n"
               f"  {PREFIX}eval --read test.py\n"
               f"  {PREFIX}eval --run test.py")
        return
    
    # Chỉnh sửa file
    if code.startswith("--file "):
        parts = code[7:].strip().split(maxsplit=1)
        if len(parts) < 2:
            _reply(client, message_object, thread_id, thread_type, "❌ --file <đường dẫn> <nội dung>")
            return
        filepath = parts[0]
        content = parts[1]
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            _reply(client, message_object, thread_id, thread_type, f"✅ Đã lưu: {filepath}\n📝 {len(content)} ký tự")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)}")
        return
    
    # Đọc file
    if code.startswith("--read "):
        filepath = code[7:].strip()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 1500:
                tmp = f"/storage/emulated/0/temp_read.txt"
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(content)
                client.sendLocalFile(tmp, thread_id=thread_id, thread_type=thread_type)
                os.remove(tmp)
            else:
                _reply(client, message_object, thread_id, thread_type, content)
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, f"❌ {str(e)}")
        return
    
    # Chạy file
    if code.startswith("--run "):
        filepath = code[6:].strip()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
            
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            namespace = {
                'client': client,
                'msg': message_object,
                'author_id': author_id,
                'thread_id': thread_id,
                'thread_type': thread_type,
            }
            exec(file_content, namespace)
            output = sys.stdout.getvalue()
            result = namespace.get('result', None)
            
            sys.stdout = old_stdout
            
            if output:
                _reply(client, message_object, thread_id, thread_type, output.strip()[:1000])
            elif result is not None:
                _reply(client, message_object, thread_id, thread_type, str(result)[:1000])
            else:
                _reply(client, message_object, thread_id, thread_type, "✅ Done")
        except Exception as e:
            _reply(client, message_object, thread_id, thread_type, traceback.format_exc()[:1000])
        return
    
    # Chạy code trực tiếp
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        namespace = {
            'client': client,
            'msg': message_object,
            'author_id': author_id,
            'thread_id': thread_id,
            'thread_type': thread_type,
            'open': open,
            'os': os,
            'sys': sys,
        }
        exec(code, namespace)
        output = sys.stdout.getvalue()
        result = namespace.get('result', None)
        
        if output:
            _reply(client, message_object, thread_id, thread_type, output.strip()[:1000])
        elif result is not None:
            _reply(client, message_object, thread_id, thread_type, str(result)[:1000])
        else:
            _reply(client, message_object, thread_id, thread_type, "✅ Done")
    except Exception as e:
        _reply(client, message_object, thread_id, thread_type, traceback.format_exc()[:1000])
    finally:
        sys.stdout = old_stdout

def LIGHT():
    return {"eval": handle_eval}