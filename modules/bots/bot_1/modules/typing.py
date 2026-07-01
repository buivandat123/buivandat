# modules/typing.py
# -*- coding: utf-8 -*-
import time
import threading
from zlapi.models import Message, ThreadType

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Bật/tắt typing indicator",
    "power": "User"
}

typing_threads = {}

def handle_typing(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        client.replyMessage(
            Message(text="""📝 HƯỚNG DẪN TYPING
━━━━━━━━━━━━━━━━━━━━
.typing on              - Bật typing nhóm này
.typing off             - Tắt typing nhóm này
.typing @user           - Bật typing cho user
.typing @user 5         - Bật typing user (delay 5s)
.typing off @user       - Tắt typing cho user
.typing --group on all  - Bật typing tất cả nhóm
.typing --group off all - Tắt typing tất cả nhóm

💡 Mặc định delay: 2 giây
"""),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # ===== KIỂM TRA MENTION =====
    if message_object.mentions:
        target_uid = message_object.mentions[0]['uid']
        delay = 2
        
        if len(parts) > 1:
            if parts[1].lower() == "off":
                action = "off"
                if len(parts) > 2 and parts[2].isdigit():
                    delay = int(parts[2])
            elif parts[1].isdigit():
                action = "on"
                delay = int(parts[1])
            else:
                action = "on"
                if len(parts) > 2 and parts[2].isdigit():
                    delay = int(parts[2])
        else:
            action = "on"
        
        if delay < 1:
            delay = 1
        if delay > 30:
            delay = 30
        
        key = f"{target_uid}_{ThreadType.USER}"
        
        # ===== TẮT TYPING CHO USER =====
        if action == "off":
            if key in typing_threads:
                typing_threads[key]["stop"] = True
                del typing_threads[key]
                client.replyMessage(
                    Message(text="✅ Đã tắt typing cho user."),
                    message_object, thread_id, thread_type, ttl=60000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ Typing chưa được bật cho user này."),
                    message_object, thread_id, thread_type, ttl=60000
                )
            return
        
        # ===== BẬT TYPING CHO USER =====
        if key in typing_threads:
            typing_threads[key]["stop"] = True
            time.sleep(0.5)
        
        stop_flag = {"stop": False}
        typing_threads[key] = stop_flag
        
        def do_typing_user(uid, stop_flag, delay):
            while not stop_flag["stop"]:
                try:
                    client.setTyping(uid, ThreadType.USER)
                    time.sleep(delay)
                except:
                    break
        
        threading.Thread(target=do_typing_user, args=(target_uid, stop_flag, delay), daemon=True).start()
        client.replyMessage(
            Message(text=f"✅ Đã bật typing cho user (delay {delay}s)."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # ===== LỆNH BÌNH THƯỜNG =====
    target = None
    action = None
    is_all = False
    delay = 2
    
    if len(parts) >= 3 and parts[1].startswith("--"):
        target = parts[1].lower()
        action = parts[2].lower()
        is_all = len(parts) > 3 and parts[3].lower() == "all"
        if is_all and len(parts) > 4 and parts[4].isdigit():
            delay = int(parts[4])
        elif not is_all and len(parts) > 3 and parts[3].isdigit():
            delay = int(parts[3])
    else:
        action = parts[1].lower()
        is_all = len(parts) > 2 and parts[2].lower() == "all"
        if is_all and len(parts) > 3 and parts[3].isdigit():
            delay = int(parts[3])
        elif not is_all and len(parts) > 2 and parts[2].isdigit():
            delay = int(parts[2])
    
    if delay < 1:
        delay = 1
    if delay > 30:
        delay = 30
    
    # ===== GROUP ON ALL =====
    if target == "--group" and action == "on" and is_all:
        try:
            groups = client.fetchAllGroups()
            group_ids = list(groups.gridVerMap.keys()) if hasattr(groups, "gridVerMap") else []
        except:
            group_ids = []
        
        if not group_ids:
            client.replyMessage(
                Message(text="❌ Không lấy được danh sách nhóm."),
                message_object, thread_id, thread_type, ttl=60000
            )
            return
        
        count = 0
        for gid in group_ids:
            key = f"{gid}_{ThreadType.GROUP}"
            
            if key in typing_threads:
                typing_threads[key]["stop"] = True
                time.sleep(0.05)
            
            stop_flag = {"stop": False}
            typing_threads[key] = stop_flag
            
            def do_typing_group(gid, stop_flag, delay):
                while not stop_flag["stop"]:
                    try:
                        client.setTyping(gid, ThreadType.GROUP)
                        time.sleep(delay)
                    except:
                        break
            
            threading.Thread(target=do_typing_group, args=(gid, stop_flag, delay), daemon=True).start()
            count += 1
        
        client.replyMessage(
            Message(text=f"✅ Đã bật typing cho {count} nhóm (delay {delay}s)."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # ===== GROUP OFF ALL =====
    if target == "--group" and action == "off" and is_all:
        count = 0
        for key in list(typing_threads.keys()):
            if key.endswith(f"_{ThreadType.GROUP}"):
                typing_threads[key]["stop"] = True
                del typing_threads[key]
                count += 1
        
        client.replyMessage(
            Message(text=f"✅ Đã tắt typing cho {count} nhóm."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # ===== ON/OFF NHÓM HIỆN TẠI =====
    key = f"{thread_id}_{thread_type}"
    
    if action == "on":
        if key in typing_threads:
            typing_threads[key]["stop"] = True
            time.sleep(0.5)
        
        stop_flag = {"stop": False}
        typing_threads[key] = stop_flag
        
        def do_typing():
            while not stop_flag["stop"]:
                try:
                    client.setTyping(thread_id, thread_type)
                    time.sleep(delay)
                except:
                    break
        
        threading.Thread(target=do_typing, daemon=True).start()
        client.replyMessage(
            Message(text=f"✅ Đã bật typing (delay {delay}s)."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    if action == "off":
        if key in typing_threads:
            typing_threads[key]["stop"] = True
            del typing_threads[key]
            client.replyMessage(Message(text="✅ Đã tắt typing."), message_object, thread_id, thread_type, ttl=60000)
        else:
            client.replyMessage(Message(text="⚠️ Typing chưa được bật."), message_object, thread_id, thread_type, ttl=60000)
        return
    
    client.replyMessage(Message(text="❌ Sai lệnh."), message_object, thread_id, thread_type, ttl=60000)

def Kryzis():
    return {"typing": handle_typing}