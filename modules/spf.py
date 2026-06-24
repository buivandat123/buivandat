import os
import json
import time
import threading
import random
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.0',
    'credits': 'kryzis X TXA',
    'description': 'Spam full chức năng Zalo - text, sticker, reaction, poll (cực nhanh)',
    'power': 'Admin'
}

FONT_SIZE = "9"
CACHE_DIR = "modules/cache/spf"
os.makedirs(CACHE_DIR, exist_ok=True)

spam_tasks = {}

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

# Sticker list
STICKERS = [
    {"sticker_type": 3, "sticker_id": "23311", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "27598", "category_id": "10746"},
    {"sticker_type": 3, "sticker_id": "28564", "category_id": "10877"},
    {"sticker_type": 3, "sticker_id": "29208", "category_id": "10990"},
]

# Reaction list
REACTIONS = ["❤️", "👍", "😂", "😢", "😱", "😍", "🎉", "🔥", "💯", "✅", "❌", "👎", "😎", "🥰", "😭"]

# Default spam texts
TEXTS = [
    "🔥",
    "💯",
    "🎉",
    "🚀",
    "⚡",
    "✅",
    "❌",
    "😎",
    "🥰",
    "🤣",
    "SPAM!",
    "BOT",
    "ZALO",
    "123",
    "ABC"
]

def load_texts():
    try:
        with open(CACHE_DIR + "/texts.txt", "r", encoding="utf-8") as f:
            texts = [line.strip() for line in f if line.strip()]
            if texts:
                return texts
    except:
        pass
    return TEXTS

def load_stickers():
    try:
        with open(CACHE_DIR + "/stickers.json", "r", encoding="utf-8") as f:
            stickers = json.load(f)
            if stickers:
                return stickers
    except:
        pass
    return STICKERS

def save_stickers(stickers):
    with open(CACHE_DIR + "/stickers.json", "w", encoding="utf-8") as f:
        json.dump(stickers, f, ensure_ascii=False, indent=2)

# Poll questions
POLL_QUESTIONS = [
    "Bạn có thích bot không?",
    "Spam?",
    "OK?",
    "Yes/No?"
]
POLL_OPTIONS = ["Có", "Không"]

def spam_worker(client, thread_id, thread_type, mode, count, delay, stop_event, task_id, message_object=None):
    """Worker spam"""
    texts = load_texts()
    stickers = load_stickers()
    
    sent = 0
    failed = 0
    idx = 0
    
    while not stop_event.is_set() and sent < count:
        try:
            if mode == "text" or mode == "all":
                text = random.choice(texts)
                client.send(Message(text=text), thread_id=thread_id, thread_type=thread_type, ttl=60000)
                sent += 1
                time.sleep(delay)
            
            if mode == "sticker" or mode == "all":
                sticker = random.choice(stickers)
                client.sendSticker(
                    sticker['sticker_type'],
                    sticker['sticker_id'],
                    sticker['category_id'],
                    thread_id,
                    thread_type
                )
                sent += 1
                time.sleep(delay)
            
            if mode == "reaction" or mode == "all":
                if message_object:
                    reaction = random.choice(REACTIONS)
                    client.sendReaction(message_object, reaction, thread_id, thread_type, reactionType=75)
                    sent += 1
                    time.sleep(delay)
            
            if mode == "poll" or mode == "all":
                question = random.choice(POLL_QUESTIONS)
                client.createPoll(question=question, options=POLL_OPTIONS, groupId=thread_id)
                sent += 1
                time.sleep(delay)
            
            idx += 1
            
        except Exception as e:
            failed += 1
            print(f"[SPF] Lỗi: {e}")
            time.sleep(delay)
    
    if task_id in spam_tasks:
        del spam_tasks[task_id]
    
    result_msg = f"""
📊 KẾT THÚC SPF
━━━━━━━━━━━━━━━━━━━━━━
✅ Thành công: {sent}
❌ Thất bại: {failed}
🎯 Loại: {mode.upper()}
━━━━━━━━━━━━━━━━━━━━━━
🛑 Dừng: .spf stop
    """
    try:
        client.send(Message(text=result_msg.strip(), style=_sty(result_msg, "#15A85F")), thread_id=thread_id, thread_type=thread_type, ttl=60000)
    except:
        pass

def handle_spf_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("spf"):
        return
    
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền!", style=_sty("❌ Bạn không có quyền!", "#DB342E")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    content = cmd[3:].strip()
    parts = content.split()
    
    # STOP
    if content.lower() == "stop":
        task_id = str(thread_id)
        if task_id in spam_tasks:
            spam_tasks[task_id].set()
            client.replyMessage(
                Message(text="✅ Đã dừng spf!", style=_sty("✅ Đã dừng!", "#15A85F")),
                message_object, thread_id, thread_type, ttl=30000
            )
        else:
            client.replyMessage(
                Message(text="❌ Không có spf nào đang chạy!", style=_sty("❌ Không có!", "#DB342E")),
                message_object, thread_id, thread_type, ttl=30000
            )
        return
    
    # ADD TEXT
    if content.startswith("addtext "):
        new_text = content[8:].strip()
        if new_text:
            texts = load_texts()
            texts.append(new_text)
            with open(CACHE_DIR + "/texts.txt", "w", encoding="utf-8") as f:
                for t in texts:
                    f.write(t + "\n")
            client.replyMessage(
                Message(text=f"✅ Đã thêm text:\n📝 {new_text[:50]}", style=_sty("✅ Đã thêm!", "#15A85F")),
                message_object, thread_id, thread_type, ttl=30000
            )
        return
    
    # ADD STICKER
    if content.startswith("addsticker "):
        parts_sticker = content[11:].split()
        if len(parts_sticker) >= 3:
            sticker = {
                "sticker_type": int(parts_sticker[0]),
                "sticker_id": parts_sticker[1],
                "category_id": parts_sticker[2]
            }
            stickers = load_stickers()
            stickers.append(sticker)
            save_stickers(stickers)
            client.replyMessage(
                Message(text=f"✅ Đã thêm sticker!\n📦 ID: {parts_sticker[1]}", style=_sty("✅ Đã thêm!", "#15A85F")),
                message_object, thread_id, thread_type, ttl=30000
            )
        else:
            client.replyMessage(
                Message(text="❌ Cú pháp: .spf addsticker <type> <id> <category>", style=_sty("❌ Sai cú pháp!", "#DB342E")),
                message_object, thread_id, thread_type, ttl=30000
            )
        return
    
    # LIST TEXT
    if content.lower() == "listtext":
        texts = load_texts()
        if not texts:
            client.replyMessage(Message(text="📭 Chưa có text nào!"), message_object, thread_id, thread_type, ttl=30000)
            return
        lines = ["📋 DANH SÁCH TEXT SPAM", "━━━━━━━━━━━━━━━━━━━━━━"]
        for i, t in enumerate(texts[:30], 1):
            lines.append(f"{i}. {t[:50]}")
        client.replyMessage(Message(text="\n".join(lines)), message_object, thread_id, thread_type, ttl=60000)
        return
    
    # LIST STICKER
    if content.lower() == "liststicker":
        stickers = load_stickers()
        if not stickers:
            client.replyMessage(Message(text="📭 Chưa có sticker nào!"), message_object, thread_id, thread_type, ttl=30000)
            return
        lines = ["📋 DANH SÁCH STICKER", "━━━━━━━━━━━━━━━━━━━━━━"]
        for i, s in enumerate(stickers[:20], 1):
            lines.append(f"{i}. Type: {s['sticker_type']}, ID: {s['sticker_id']}")
        client.replyMessage(Message(text="\n".join(lines)), message_object, thread_id, thread_type, ttl=60000)
        return
    
    # CLEAR
    if content.lower() == "clear":
        with open(CACHE_DIR + "/texts.txt", "w", encoding="utf-8") as f:
            for t in TEXTS:
                f.write(t + "\n")
        save_stickers(STICKERS)
        client.replyMessage(
            Message(text="✅ Đã reset danh sách text và sticker!", style=_sty("✅ Đã reset!", "#15A85F")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # HELP
    if not parts:
        help_text = f"""
📊 SPF - SPAM FULL CỰC NHANH

Cách dùng:
{prefix}spf <số_lần> <delay> <mode>
{prefix}spf stop

Mode:
- text     : Chỉ spam text
- sticker  : Chỉ spam sticker
- reaction : Chỉ spam reaction
- poll     : Chỉ spam poll
- all      : Tất cả (mặc định)

Thêm nội dung:
{prefix}spf addtext <nội dung>
{prefix}spf addsticker <type> <id> <category>
{prefix}spf listtext
{prefix}spf liststicker
{prefix}spf clear

Ví dụ:
{prefix}spf 100 0.01 text
{prefix}spf 50 0.02 all
{prefix}spf stop
        """
        client.replyMessage(
            Message(text=help_text.strip(), style=_sty(help_text, "#00BFFF")),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # SPAM FULL
    try:
        count = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 10
        delay = float(parts[1].replace(',', '.')) if len(parts) > 1 else 0.01
        mode = parts[2].lower() if len(parts) > 2 else "all"
        
        if mode not in ["text", "sticker", "reaction", "poll", "all"]:
            mode = "all"
        
        if count > 500:
            count = 500
            client.replyMessage(
                Message(text="⚠️ Giới hạn tối đa 500 lần!", style=_sty("⚠️ Giới hạn 500!", "#F7B503")),
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
            Message(text="❌ Cú pháp: .spf <số_lần> <delay> <mode>", style=_sty("❌ Sai cú pháp!", "#DB342E")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Kiểm tra task
    task_id = str(thread_id)
    if task_id in spam_tasks:
        client.replyMessage(
            Message(text="⚠️ Đang có spf chạy! Dùng .spf stop trước.", style=_sty("⚠️ Đang có spf!", "#F7B503")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Thông báo
    total_time = count * delay
    msg = f"""
📊 BẮT ĐẦU SPF
━━━━━━━━━━━━━━━━━━━━━━
🔁 Số lần: {count}
⏱️ Delay: {delay}s
🎯 Loại: {mode.upper()}
⏰ Dự kiến: {total_time:.1f}s
━━━━━━━━━━━━━━━━━━━━━━
🛑 Dừng: {prefix}spf stop
    """
    client.replyMessage(
        Message(text=msg.strip(), style=_sty(msg, "#15A85F")),
        message_object, thread_id, thread_type, ttl=30000
    )
    
    # Tạo task
    stop_event = threading.Event()
    spam_tasks[task_id] = stop_event
    
    thread = threading.Thread(
        target=spam_worker,
        args=(client, thread_id, thread_type, mode, count, delay, stop_event, task_id, message_object),
        daemon=True
    )
    thread.start()

def Kryzis():
    return {"spf": handle_spf_command}