# modules/autoreply.py
# -*- coding: utf-8 -*-
import os
import json
import requests
import urllib.parse
import time
import threading
import random
from zlapi.models import Message, ThreadType

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Tự động trả lời khi được nhắc đến 'kryzis'",
    "power": "Admin"
}

CONFIG_FILE = "modules/cache/autoreply_config.json"
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

KEYWORDS = [
    "kryzis", "kryzis ơi", "kryzis oi", "ơi kryzis", "oi kryzis",
    "@kryzis", "#kryzis", "kryzis này", "kryzis à", "kryzis đâu",
    "em kryzis", "chị kryzis", "anh kryzis", "bé kryzis"
]

CUTE_CHARS = ["=))", "=))", ":)", "=))", "-.-", "^^", ":3", "hihi", "hehe", "nè", "nha", "ạ", "❤️", "✨"]

# Cooldown settings
COOLDOWN_TIME = 30  # giây
user_cooldown = {}  # Lưu thời gian cooldown của từng user
thread_cooldown = {}  # Lưu thời gian cooldown của từng nhóm
processed_messages = set()  # Lưu ID tin nhắn đã xử lý

# Emoji đếm ngược
COUNTDOWN_EMOJIS = {
    30: "🕐",
    29: "🕐",
    28: "🕐",
    27: "🕐",
    26: "🕐",
    25: "🕐",
    24: "🕑",
    23: "🕑",
    22: "🕑",
    21: "🕑",
    20: "🕑",
    19: "🕒",
    18: "🕒",
    17: "🕒",
    16: "🕒",
    15: "🕒",
    14: "🕓",
    13: "🕓",
    12: "🕓",
    11: "🕓",
    10: "🕓",
    9: "🕔",
    8: "🕔",
    7: "🕔",
    6: "🕕",
    5: "🕕",
    4: "🕖",
    3: "🕗",
    2: "🕘",
    1: "🕙",
    0: "🕛"
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_enabled(thread_id):
    config = load_config()
    return config.get(str(thread_id), {}).get('enabled', False)

def set_enabled(thread_id, enabled):
    config = load_config()
    if str(thread_id) not in config:
        config[str(thread_id)] = {}
    config[str(thread_id)]['enabled'] = enabled
    save_config(config)

def call_chatgpt(message):
    try:
        prompt = f"Bạn là Kryzis, hãy trả lời câu hỏi này với phong cách: mỉa mai và cãi lại khi ai đó chửi, dễ thương và tốt bụng khi ai đó nói chuyện tử tế. Dùng các biểu cảm như =)), :), =)), -.-, ^^, :3, hihi, hehe, nè, nha, ạ. Câu hỏi: {message}"
        
        encoded = urllib.parse.quote(prompt)
        url = f"https://nqduan.id.vn/api/chatgpt?ask={encoded}&version=v1"
        
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                return data.get('response', 'Xin lỗi, tôi không hiểu!')
    except:
        pass
    return None

def add_cute_chars(text):
    if not text:
        return text
    has_char = any(char in text for char in CUTE_CHARS)
    if not has_char:
        num = random.randint(1, 2)
        chars = random.sample(CUTE_CHARS, num)
        text += " " + " ".join(chars)
    return text

def get_remaining_time(thread_id, author_id):
    """Lấy thời gian còn lại của cooldown"""
    current_time = time.time()
    
    # Kiểm tra cooldown nhóm
    if thread_id in thread_cooldown:
        elapsed = current_time - thread_cooldown[thread_id]
        if elapsed < COOLDOWN_TIME:
            return int(COOLDOWN_TIME - elapsed)
    
    # Kiểm tra cooldown user
    if author_id in user_cooldown:
        elapsed = current_time - user_cooldown[author_id]
        if elapsed < COOLDOWN_TIME:
            return int(COOLDOWN_TIME - elapsed)
    
    return 0

def is_on_cooldown(thread_id, author_id):
    """Kiểm tra cooldown"""
    current_time = time.time()
    
    # Kiểm tra cooldown nhóm
    if thread_id in thread_cooldown:
        if current_time - thread_cooldown[thread_id] < COOLDOWN_TIME:
            return True, "group"
    
    # Kiểm tra cooldown user
    if author_id in user_cooldown:
        if current_time - user_cooldown[author_id] < COOLDOWN_TIME:
            return True, "user"
    
    return False, None

def update_cooldown(thread_id, author_id):
    """Cập nhật thời gian cooldown"""
    current_time = time.time()
    thread_cooldown[thread_id] = current_time
    user_cooldown[author_id] = current_time

def start_countdown_reaction(message_object, client, thread_id, thread_type):
    """Bắt đầu đếm ngược bằng reaction"""
    try:
        # Lấy message_id từ message_object
        msg_id = message_object.id if hasattr(message_object, 'id') else None
        if not msg_id:
            return
        
        # Bắt đầu đếm ngược từ 30 giây
        for i in range(COOLDOWN_TIME, -1, -1):
            # Lấy emoji tương ứng
            emoji = COUNTDOWN_EMOJIS.get(i, "🕐")
            
            # Gửi reaction
            try:
                client.reactToMessage(msg_id, emoji, thread_id, thread_type)
            except:
                pass
            
            # Chờ 1 giây
            time.sleep(1)
        
        # Thả reaction xong (hoặc xóa reaction nếu muốn)
        # client.unreactToMessage(msg_id, thread_id, thread_type)
        
    except Exception as e:
        pass

# ========== LỆNH ON/OFF ==========
def handle_autoreply(message, message_object, thread_id, thread_type, author_id, client):
    """Lệnh chính: autoreply on/off/status/test"""
    if thread_type != ThreadType.GROUP:
        client.replyMessage(Message(text="❌ Chỉ dùng trong nhóm!"), 
                          message_object, thread_id, thread_type, ttl=60000)
        return
    
    parts = message.strip().split()
    if len(parts) < 2:
        status = "BẬT ✅" if is_enabled(thread_id) else "TẮT ❌"
        
        # Hiển thị cooldown trong status
        remaining = get_remaining_time(thread_id, author_id)
        cooldown_text = ""
        if remaining > 0:
            cooldown_text = f"\n\n⏳ Đếm ngược: {remaining}s"
        
        msg = f"""📊 AUTOREPLY

Trạng thái: {status}{cooldown_text}

• autoreply on  - Bật
• autoreply off - Tắt
• autoreply test <câu hỏi> - Test
"""
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
        return
    
    cmd = parts[1].lower()
    
    if cmd == "on":
        set_enabled(thread_id, True)
        client.replyMessage(Message(text="✅ Đã bật autoreply!\nKhi nhắc 'kryzis' bot sẽ trả lời =))"), 
                          message_object, thread_id, thread_type, ttl=60000)
    
    elif cmd == "off":
        set_enabled(thread_id, False)
        client.replyMessage(Message(text="❌ Đã tắt autoreply!"), 
                          message_object, thread_id, thread_type, ttl=60000)
    
    elif cmd == "test":
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Nhập câu hỏi!\nVD: autoreply test Xin chào"), 
                              message_object, thread_id, thread_type, ttl=60000)
            return
        
        query = " ".join(parts[2:])
        client.replyMessage(Message(text=f"⏳ Đang hỏi Kryzis..."), 
                          message_object, thread_id, thread_type, ttl=30000)
        
        response = call_chatgpt(query)
        if response:
            response = add_cute_chars(response)
            client.replyMessage(Message(text=f"🤖 {response}"), 
                              message_object, thread_id, thread_type, ttl=60000)
        else:
            client.replyMessage(Message(text="❌ Lỗi gọi API!"), 
                              message_object, thread_id, thread_type, ttl=60000)
    
    else:
        client.replyMessage(Message(text="❌ autoreply on/off/test"), 
                          message_object, thread_id, thread_type, ttl=60000)

def handle_autoreply_message(message_text, message_object, thread_id, thread_type, author_id, client):
    """Xử lý tin nhắn không prefix - bắt 'kryzis'"""
    if thread_type != ThreadType.GROUP:
        return False
    
    if not is_enabled(thread_id):
        return False
    
    # Kiểm tra tin nhắn từ bot
    if hasattr(message_object, 'author') and hasattr(message_object.author, 'id'):
        if message_object.author.id == client.user_id:
            return False
    
    # Kiểm tra tin nhắn đã xử lý chưa
    msg_id = message_object.id if hasattr(message_object, 'id') else None
    if msg_id and msg_id in processed_messages:
        return False
    
    text = message_text.lower().strip()
    
    has_keyword = False
    for kw in KEYWORDS:
        if kw in text:
            has_keyword = True
            break
    
    if not has_keyword:
        return False
    
    # Lưu ID tin nhắn đã xử lý
    if msg_id:
        processed_messages.add(msg_id)
        threading.Timer(600, lambda: processed_messages.discard(msg_id)).start()
    
    # Kiểm tra cooldown
    on_cooldown, cooldown_type = is_on_cooldown(thread_id, author_id)
    if on_cooldown:
        remaining = get_remaining_time(thread_id, author_id)
        
        # Bắt đầu đếm ngược bằng reaction
        threading.Thread(
            target=start_countdown_reaction,
            args=(message_object, client, thread_id, thread_type),
            daemon=True
        ).start()
        
        # Gửi tin nhắn thông báo
        client.replyMessage(
            Message(text=f"⏳ Đang đếm ngược... Còn {remaining}s nữa nhé!"),
            message_object, thread_id, thread_type, ttl=5000
        )
        return False
    
    # Cập nhật cooldown
    update_cooldown(thread_id, author_id)
    
    # Bắt đầu đếm ngược reaction ngay khi bot trả lời
    threading.Thread(
        target=start_countdown_reaction,
        args=(message_object, client, thread_id, thread_type),
        daemon=True
    ).start()
    
    query = message_text.strip()
    for kw in KEYWORDS:
        query = query.replace(kw, "").strip()
    
    if not query:
        query = "Chào Kryzis!"
    
    def send_response():
        try:
            try:
                client.setTyping(thread_id, thread_type)
            except:
                pass
            
            response = call_chatgpt(query)
            if response:
                response = add_cute_chars(response)
            else:
                fallback = [
                    "Kryzis đây! Có gì không =))",
                    "Hửm? Gọi Kryzis hả :3",
                    "Có em đây! Nói gì đi nè!",
                    "Kryzis nghe đây! =))",
                    "Alo alo! Kryzis đây nè!",
                    "Gọi em à? Có gì vui không ^^",
                    "Em đây! Có gì kể em nghe với! hihi"
                ]
                response = random.choice(fallback)
            
            # Thay thế từ khóa trong response để tránh tự kích hoạt
            for kw in KEYWORDS:
                if kw.lower() in response.lower():
                    response = response.replace(kw, "Kryzis")
                    break
            
            client.sendMessage(Message(text=f"🤖 {response}"), 
                             thread_id=thread_id, thread_type=thread_type, ttl=60000)
        except:
            pass
    
    threading.Thread(target=send_response, daemon=True).start()
    return True

def Kryzis():
    return {
        "autoreply": handle_autoreply,
        "_noprefix": handle_autoreply_message
    }