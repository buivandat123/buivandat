import os
import json
import time
import threading
import random
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.0',
    'credits': 'kryzis X TXA',
    'description': 'Spam tạo poll tự động - tốc độ cực nhanh',
    'power': 'Admin'
}

FONT_SIZE = "9"
CACHE_DIR = "modules/cache/spoll"
os.makedirs(CACHE_DIR, exist_ok=True)

spam_poll_tasks = {}

def _sty(text, color="#e8eaf6"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=FONT_SIZE, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def is_admin(author_id):
    try:
        with open("asset/seting.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            owner = str(data.get("admin", ""))
            admins = [str(x) for x in data.get("adm", [])]
            return str(author_id) == owner or str(author_id) in admins
    except:
        try:
            from asset.config import ADMIN
            return str(author_id) == str(ADMIN)
        except:
            return False

# Danh sách câu hỏi poll
QUESTIONS = [
    "Bạn có thích bot này không?",
    "Hôm nay bạn thế nào?",
    "Bạn đang làm gì?",
    "Thời tiết hôm nay thế nào?",
    "Bạn có đói không?",
    "Bạn có thích ăn phở không?",
    "Bạn có thích mèo không?",
    "Bạn có thích chó không?",
    "Bạn có thích mưa không?",
    "Bạn có thích nắng không?"
]

# Danh sách options
OPTIONS_LIST = [
    ["Có", "Không"],
    ["Rất thích", "Bình thường", "Không thích"],
    ["Tuyệt vời", "Ổn", "Tệ"],
    ["Vui", "Buồn", "Bình thường"],
    ["✅", "❌"],
    ["👍", "👎"]
]

def load_questions():
    try:
        with open(CACHE_DIR + "/questions.txt", "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]
            if questions:
                return questions
    except:
        pass
    return QUESTIONS

def load_options():
    try:
        with open(CACHE_DIR + "/options.txt", "r", encoding="utf-8") as f:
            options = []
            for line in f:
                if line.strip():
                    opts = [opt.strip() for opt in line.split('|')]
                    if opts:
                        options.append(opts)
            if options:
                return options
    except:
        pass
    return OPTIONS_LIST

def poll_worker(client, thread_id, thread_type, count, delay, stop_event, task_id):
    questions = load_questions()
    options_list = load_options()
    
    sent = 0
    failed = 0
    
    while not stop_event.is_set() and sent < count:
        try:
            question = random.choice(questions)
            options = random.choice(options_list)
            
            result = client.createPoll(
                question=question,
                options=options,
                groupId=thread_id
            )
            
            if result and result.get('error_code') == 0:
                sent += 1
                print(f"[SPOLL] Đã tạo poll {sent}/{count}")
            else:
                failed += 1
            
            time.sleep(delay)
            
        except Exception as e:
            failed += 1
            print(f"[SPOLL] Lỗi: {e}")
            time.sleep(delay)
    
    result_msg = f"""
📊 KẾT THÚC SPOLL
━━━━━━━━━━━━━━━━━━━━━━
✅ Thành công: {sent}
❌ Thất bại: {failed}
📊 Tổng: {sent + failed}
━━━━━━━━━━━━━━━━━━━━━━
🛑 Dừng: .spoll stop
    """
    try:
        client.send(Message(text=result_msg.strip(), style=_sty(result_msg, "#15A85F")), thread_id=thread_id, thread_type=thread_type, ttl=60000)
    except:
        pass
    
    if task_id in spam_poll_tasks:
        del spam_poll_tasks[task_id]

def handle_spoll_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("spoll"):
        return
    
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền!", style=_sty("❌ Bạn không có quyền!", "#DB342E")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    content = cmd[5:].strip()
    parts = content.split()
    
    # STOP
    if content.lower() == "stop":
        task_id = str(thread_id)
        if task_id in spam_poll_tasks:
            spam_poll_tasks[task_id].set()
            client.replyMessage(
                Message(text="✅ Đã dừng spoll!", style=_sty("✅ Đã dừng!", "#15A85F")),
                message_object, thread_id, thread_type, ttl=30000
            )
        else:
            client.replyMessage(
                Message(text="❌ Không có spoll nào đang chạy!", style=_sty("❌ Không có!", "#DB342E")),
                message_object, thread_id, thread_type, ttl=30000
            )
        return
    
    # SET QUESTIONS
    if content.startswith("addq "):
        new_question = content[5:].strip()
        if new_question:
            questions = load_questions()
            if new_question not in questions:
                questions.append(new_question)
                with open(CACHE_DIR + "/questions.txt", "w", encoding="utf-8") as f:
                    for q in questions:
                        f.write(q + "\n")
                client.replyMessage(
                    Message(text=f"✅ Đã thêm câu hỏi:\n📝 {new_question[:50]}", style=_sty("✅ Đã thêm!", "#15A85F")),
                    message_object, thread_id, thread_type, ttl=30000
                )
            else:
                client.replyMessage(
                    Message(text="❌ Câu hỏi đã tồn tại!", style=_sty("❌ Đã tồn tại!", "#DB342E")),
                    message_object, thread_id, thread_type, ttl=30000
                )
        return
    
    # SET OPTIONS
    if content.startswith("addopt "):
        new_options = content[7:].strip()
        if new_options:
            opts = [opt.strip() for opt in new_options.split('|')]
            if len(opts) >= 2:
                options_list = load_options()
                options_list.append(opts)
                with open(CACHE_DIR + "/options.txt", "w", encoding="utf-8") as f:
                    for opt in options_list:
                        f.write("|".join(opt) + "\n")
                client.replyMessage(
                    Message(text=f"✅ Đã thêm options:\n📝 {' | '.join(opts)}", style=_sty("✅ Đã thêm!", "#15A85F")),
                    message_object, thread_id, thread_type, ttl=30000
                )
            else:
                client.replyMessage(
                    Message(text="❌ Options phải có ít nhất 2 lựa chọn!\nVD: Có|Không", style=_sty("❌ Lỗi!", "#DB342E")),
                    message_object, thread_id, thread_type, ttl=30000
                )
        return
    
    # LIST
    if content.lower() == "list":
        questions = load_questions()
        options_list = load_options()
        
        msg = f"""
📋 DANH SÁCH CÂU HỎI ({len(questions)})
━━━━━━━━━━━━━━━━━━━━━━
"""
        for i, q in enumerate(questions[:20], 1):
            msg += f"{i}. {q[:50]}\n"
        
        msg += f"\n📋 DANH SÁCH OPTIONS ({len(options_list)})\n"
        for i, opt in enumerate(options_list[:10], 1):
            msg += f"{i}. {' | '.join(opt)}\n"
        
        msg += f"\n💡 Thêm câu hỏi: {prefix}spoll addq <câu hỏi>"
        msg += f"\n💡 Thêm options: {prefix}spoll addopt <lựa chọn 1|lựa chọn 2|...>"
        
        client.replyMessage(
            Message(text=msg.strip(), style=_sty(msg, "#e8eaf6")),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # HELP
    if not parts:
        help_text = f"""
📊 SPOLL - TẠO POLL CỰC NHANH

{prefix}spoll <số_lần> <delay>
{prefix}spoll stop
{prefix}spoll addq <câu hỏi>
{prefix}spoll addopt <lựa chọn 1|lựa chọn 2|...>
{prefix}spoll list

Delay mặc định: 0.01s (cực nhanh)

Ví dụ:
{prefix}spoll 50 0.01   (50 poll, delay 0.01s)
{prefix}spoll stop
        """
        client.replyMessage(
            Message(text=help_text.strip(), style=_sty(help_text, "#00BFFF")),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # SPOLL
    try:
        count = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 10
        delay = float(parts[1].replace(',', '.')) if len(parts) > 1 else 0.01
        
        if count > 200:
            count = 200
            client.replyMessage(
                Message(text="⚠️ Giới hạn tối đa 200 poll!", style=_sty("⚠️ Giới hạn 200!", "#F7B503")),
                message_object, thread_id, thread_type, ttl=10000
            )
        
        if delay < 0.005:
            delay = 0.005
            client.replyMessage(
                Message(text="⚠️ Delay tối thiểu 0.005 giây!", style=_sty("⚠️ Delay min 0.005s!", "#F7B503")),
                message_object, thread_id, thread_type, ttl=10000
            )
        
    except:
        client.replyMessage(
            Message(text="❌ Cú pháp: .spoll <số_lần> <delay>", style=_sty("❌ Sai cú pháp!", "#DB342E")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Kiểm tra task đang chạy
    task_id = str(thread_id)
    if task_id in spam_poll_tasks:
        client.replyMessage(
            Message(text="⚠️ Đang có spoll chạy! Dùng .spoll stop trước.", style=_sty("⚠️ Đang có spoll!", "#F7B503")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Thông báo
    total_time = count * delay
    msg = f"""
📊 BẮT ĐẦU SPOLL
━━━━━━━━━━━━━━━━━━━━━━
🔁 Số poll: {count}
⏱️ Delay: {delay}s
⏰ Dự kiến: {total_time:.1f}s
━━━━━━━━━━━━━━━━━━━━━━
🛑 Dừng: {prefix}spoll stop
    """
    client.replyMessage(
        Message(text=msg.strip(), style=_sty(msg, "#15A85F")),
        message_object, thread_id, thread_type, ttl=30000
    )
    
    # Tạo task mới
    stop_event = threading.Event()
    spam_poll_tasks[task_id] = stop_event
    
    thread = threading.Thread(
        target=poll_worker,
        args=(client, thread_id, thread_type, count, delay, stop_event, task_id),
        daemon=True
    )
    thread.start()

def LIGHT():
    return {"spoll": handle_spoll_command}