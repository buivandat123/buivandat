# -*- coding: utf-8 -*-
import time
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_admin

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Chống spam prefix gây die bot",
    'power': "System"
}

# Lưu trữ thông tin spam
spam_data = {}  # {thread_id: {"count": 0, "first_time": 0, "blocked_until": 0}}
blocked_threads = {}  # {thread_id: unlock_time}

def style_warning(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#F7B503", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def style_error(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#DB342E", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def style_success(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#15A85F", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def check_spam(thread_id, current_time):
    """Kiểm tra và xử lý spam, trả về True nếu bị block"""
    # Kiểm tra xem thread có đang bị block không
    if thread_id in blocked_threads:
        unlock_time = blocked_threads[thread_id]
        if current_time < unlock_time:
            return True  # Vẫn đang bị block
        else:
            # Hết thời gian block, xóa khỏi danh sách
            del blocked_threads[thread_id]
            if thread_id in spam_data:
                del spam_data[thread_id]
            return False
    
    # Khởi tạo dữ liệu spam cho thread nếu chưa có
    if thread_id not in spam_data:
        spam_data[thread_id] = {"count": 1, "first_time": current_time}
        return False
    
    data = spam_data[thread_id]
    time_diff = current_time - data["first_time"]
    
    # Nếu trong vòng 2 giây
    if time_diff <= 2:
        data["count"] += 1
        # Nếu spam >= 3 lần trong 2 giây
        if data["count"] >= 3:
            # Block nhóm trong 30 giây
            blocked_threads[thread_id] = current_time + 30
            del spam_data[thread_id]
            return True
    else:
        # Reset nếu quá 2 giây
        spam_data[thread_id] = {"count": 1, "first_time": current_time}
    
    return False

def handle_antispam(message, message_object, thread_id, thread_type, author_id, client):
    """Hàm này được gọi từ onMessage để kiểm tra spam"""
    # Chỉ áp dụng cho nhóm
    if thread_type != ThreadType.GROUP:
        return False
    
    # Admin được phép spam (không bị block)
    if is_admin(author_id):
        return False
    
    # Chỉ check tin nhắn bắt đầu bằng prefix
    if not message.startswith(PREFIX):
        return False
    
    current_time = time.time()
    
    # Kiểm tra spam
    if check_spam(thread_id, current_time):
        # Gửi cảnh báo và không xử lý lệnh
        msg = f"WARNING\n    Nhóm đã bị khóa do spam lệnh liên tục!\n    Vui lòng đợi 30 giây."
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)
        return True  # Trả về True để bỏ qua lệnh
    
    return False  # Không bị block, xử lý bình thường

def handle_unblock(message, message_object, thread_id, thread_type, author_id, client):
    """Lệnh mở khóa nhóm bị block (dành cho admin)"""
    if not is_admin(author_id):
        msg = "ERROR\n    Bạn không có quyền!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if thread_type != ThreadType.GROUP:
        msg = "ERROR\n    Chỉ dùng trong nhóm!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if thread_id in blocked_threads:
        del blocked_threads[thread_id]
        if thread_id in spam_data:
            del spam_data[thread_id]
        msg = "SUCCESS\n    Đã mở khóa nhóm!"
        client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
    else:
        msg = "WARNING\n    Nhóm không bị khóa!"
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)

def get_blocked_status(message, message_object, thread_id, thread_type, author_id, client):
    """Lệnh kiểm tra trạng thái khóa của nhóm"""
    if not is_admin(author_id):
        msg = "ERROR\n    Bạn không có quyền!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if thread_type != ThreadType.GROUP:
        msg = "ERROR\n    Chỉ dùng trong nhóm!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if thread_id in blocked_threads:
        unlock_time = blocked_threads[thread_id]
        remaining = int(unlock_time - time.time())
        if remaining > 0:
            msg = f"WARNING\n    Nhóm đang bị khóa!\n    Còn {remaining} giây để mở khóa."
        else:
            del blocked_threads[thread_id]
            msg = "SUCCESS\n    Nhóm không bị khóa!"
    else:
        msg = "SUCCESS\n    Nhóm không bị khóa!"
    
    client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)

def Kryzis():
    return {'unblockgroup': handle_unblock, 'blockstatus': get_blocked_status}