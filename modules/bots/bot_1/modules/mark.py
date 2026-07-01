# modules/mark.py
# -*- coding: utf-8 -*-
import time
import threading
from zlapi.models import Message, ThreadType

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tự động đánh dấu tất cả tin nhắn đã xem",
    "power": "User"
}

mark_status = {}
mark_threads = {}

def handle_mark(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        client.replyMessage(
            Message(text="""📝 HƯỚNG DẪN MARK
━━━━━━━━━━━━━━━━━━━━
.mark on   - Bật tự động đánh dấu đã xem
.mark off  - Tắt tự động đánh dấu đã xem
.mark now  - Đánh dấu tất cả tin nhắn chưa xem (1 lần)
"""),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    action = parts[1].lower()
    key = f"{thread_id}_{thread_type}"
    
    # ===== BẬT MARK =====
    if action == "on":
        if key in mark_status and mark_status[key]:
            client.replyMessage(
                Message(text="⚠️ Mark đã được bật trước đó."),
                message_object, thread_id, thread_type, ttl=60000
            )
            return
        
        mark_status[key] = True
        
        if key in mark_threads:
            mark_threads[key]["stop"] = True
            time.sleep(0.5)
        
        stop_flag = {"stop": False}
        mark_threads[key] = stop_flag
        
        def auto_mark():
            while not stop_flag["stop"]:
                try:
                    # Lấy tin nhắn (tối đa 50 tin)
                    if thread_type == ThreadType.USER:
                        messages = client.fetchUserMessages(thread_id, limit=50)
                    else:
                        messages = client.fetchGroupMessages(thread_id, limit=50)
                    
                    if messages:
                        for msg in messages:
                            if hasattr(msg, 'isRead') and not msg.isRead:
                                try:
                                    client.markAsDelivered(
                                        msgId=msg.msgId,
                                        cliMsgId=msg.clientId,
                                        senderId=msg.uidFrom,
                                        threadId=thread_id,
                                        type=thread_type,
                                        method="webchat"
                                    )
                                    time.sleep(0.3)  # Tránh spam
                                except:
                                    pass
                except:
                    pass
                
                time.sleep(2)  # Kiểm tra mỗi 2 giây
        
        threading.Thread(target=auto_mark, daemon=True).start()
        
        client.replyMessage(
            Message(text="✅ Đã bật tự động đánh dấu đã xem."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # ===== TẮT MARK =====
    if action == "off":
        if key in mark_status and mark_status[key]:
            mark_status[key] = False
            if key in mark_threads:
                mark_threads[key]["stop"] = True
                del mark_threads[key]
            client.replyMessage(
                Message(text="✅ Đã tắt tự động đánh dấu đã xem."),
                message_object, thread_id, thread_type, ttl=60000
            )
        else:
            client.replyMessage(
                Message(text="⚠️ Mark chưa được bật."),
                message_object, thread_id, thread_type, ttl=60000
            )
        return
    
    # ===== MARK NOW =====
    if action == "now":
        client.replyMessage(
            Message(text="⏳ Đang đánh dấu tin nhắn..."),
            message_object, thread_id, thread_type, ttl=30000
        )
        
        def mark_now():
            try:
                count = 0
                # Lấy tối đa 50 tin nhắn
                if thread_type == ThreadType.USER:
                    messages = client.fetchUserMessages(thread_id, limit=50)
                else:
                    messages = client.fetchGroupMessages(thread_id, limit=50)
                
                if messages:
                    for msg in messages:
                        try:
                            if hasattr(msg, 'isRead') and not msg.isRead:
                                client.markAsDelivered(
                                    msgId=msg.msgId,
                                    cliMsgId=msg.clientId,
                                    senderId=msg.uidFrom,
                                    threadId=thread_id,
                                    type=thread_type,
                                    method="webchat"
                                )
                                count += 1
                                time.sleep(0.3)
                        except:
                            pass
                
                if count > 0:
                    client.replyMessage(
                        Message(text=f"✅ Đã đánh dấu {count} tin nhắn đã xem."),
                        message_object, thread_id, thread_type, ttl=60000
                    )
                else:
                    client.replyMessage(
                        Message(text="✅ Không có tin nhắn chưa đọc."),
                        message_object, thread_id, thread_type, ttl=60000
                    )
            except Exception as e:
                client.replyMessage(
                    Message(text=f"❌ Lỗi: {str(e)[:50]}"),
                    message_object, thread_id, thread_type, ttl=60000
                )
        
        threading.Thread(target=mark_now, daemon=True).start()
        return
    
    client.replyMessage(
        Message(text="❌ Sai lệnh. Dùng: .mark on/off/now"),
        message_object, thread_id, thread_type, ttl=60000
    )

def Kryzis():
    return {"mark": handle_mark}