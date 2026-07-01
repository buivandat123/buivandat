import os
import time
import threading
import json
from zlapi.models import Message

des = {
    'version': '1.0.0',
    'credits': 'kryzis X TXA',
    'description': 'Spam text từ file - delay an toàn',
    'power': 'Admin'
}

TXT_DIR = "modules/cache/treotxt"
os.makedirs(TXT_DIR, exist_ok=True)

spam_tasks = {}
spam_active = False

def get_lines_from_file(filename):
    """Đọc nội dung từ file txt"""
    filepath = os.path.join(TXT_DIR, filename)
    
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Chào các bạn!\n")
            f.write("Đây là tin nhắn spam\n")
            f.write("Bot đang hoạt động!\n")
        return None, f"✅ Đã tạo file mẫu: {filename}\n📁 {filepath}"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f if line.strip()]
        if not lines:
            return None, "❌ File rỗng!"
        return lines, None
    except Exception as e:
        return None, f"❌ Lỗi: {e}"

def spam_worker(client, thread_id, thread_type, lines, delay, task_id):
    """Worker spam"""
    stop = spam_tasks.get(task_id)
    count = 0
    
    print(f"[Treo] Bắt đầu spam, delay={delay}s")
    
    while stop and not stop.is_set():
        for line in lines:
            if stop and stop.is_set():
                break
            try:
                client.send(Message(text=line), thread_id=thread_id, thread_type=thread_type, ttl=60000)
                count += 1
                if count % 10 == 0:
                    print(f"[Treo] Đã gửi {count} tin")
                time.sleep(delay)
            except Exception as e:
                print(f"[Treo] Lỗi: {e}")
                time.sleep(0.5)
    
    if task_id in spam_tasks:
        del spam_tasks[task_id]
    print(f"[Treo] Dừng spam, tổng số tin: {count}")

def handle_treo_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.config.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("treo"):
        return
    
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền!"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    content = cmd[4:].strip()
    
    # STOP
    if content.lower() == "stop":
        task_id = str(thread_id)
        if task_id in spam_tasks:
            spam_tasks[task_id].set()
            client.replyMessage(
                Message(text="✅ Đã dừng spam!"),
                message_object, thread_id, thread_type, ttl=30000
            )
        else:
            client.replyMessage(
                Message(text="❌ Không có spam nào đang chạy!"),
                message_object, thread_id, thread_type, ttl=30000
            )
        return
    
    # HELP
    if not content:
        help_text = f"""
📢 TREO - SPAM TEXT

Cách dùng:
{prefix}treo <file.txt> <delay>

Delay (giây) khuyến nghị:
- 0.01 = NHANH (an toàn)
- 0.05 = TRUNG BÌNH
- 0.1 = CHẬM

Ví dụ:
{prefix}treo spam.txt 0.01   (nhanh, an toàn)
{prefix}treo spam.txt 0.05
{prefix}treo spam.txt 0.1

Dừng: {prefix}treo stop

📁 File trong: {TXT_DIR}
        """
        client.replyMessage(
            Message(text=help_text.strip()),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # Tách tham số
    parts = content.split()
    filename = parts[0] if len(parts) > 0 else ""
    
    # Delay mặc định 0.01
    delay = 0.01
    if len(parts) > 1:
        try:
            delay = float(parts[1].replace(',', '.'))
            if delay < 0.005:
                delay = 0.01
                client.replyMessage(
                    Message(text="⚠️ Delay quá nhỏ! Đã tự động chỉnh về 0.01s (an toàn)"),
                    message_object, thread_id, thread_type, ttl=10000
                )
        except:
            delay = 0.01
    
    if not filename:
        client.replyMessage(
            Message(text="❌ Chưa nhập tên file!\nVD: .treo spam.txt 0.01"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Đọc file
    lines, error = get_lines_from_file(filename)
    if error:
        client.replyMessage(
            Message(text=error),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Kiểm tra spam đang chạy
    task_id = str(thread_id)
    if task_id in spam_tasks:
        client.replyMessage(
            Message(text="⚠️ Đang spam! Dùng .treo stop trước."),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Tạo task mới
    stop_event = threading.Event()
    spam_tasks[task_id] = stop_event
    
    # Chạy spam
    thread = threading.Thread(
        target=spam_worker,
        args=(client, thread_id, thread_type, lines, delay, task_id),
        daemon=True
    )
    thread.start()
    
    # Tính số tin dự kiến mỗi phút
    msgs_per_minute = int(60 / delay) if delay > 0 else 0
    
    msg = f"""
    """
    client.replyMessage(
        Message(text=msg.strip()),
        message_object, thread_id, thread_type, ttl=30000
    )

def Kryzis():
    return {"treo": handle_treo_command}