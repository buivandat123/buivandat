import os
import json
import time
import random
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.0',
    'credits': 'Yuta Bot',
    'description': 'Fake typing - Tự động trả lời khi được nhắn',
    'power': 'Admin'
}

FONT_SIZE = "9"
CACHE_DIR = "modules/cache/fake"
os.makedirs(CACHE_DIR, exist_ok=True)

fake_settings = {}

def load_settings():
    global fake_settings
    try:
        with open(CACHE_DIR + "/settings.json", "r", encoding="utf-8") as f:
            fake_settings = json.load(f)
    except:
        fake_settings = {
            "enabled": False,
            "reply_delay": 2,
            "auto_reply": "Xin chào! Tôi đang bận!",
            "random_reply": ["Mình đang bận!", "Cảm ơn bạn đã nhắn!", "Để mình trả lời sau nhé!"],
            "use_random": True,
            "mention_only": True
        }
        save_settings()

def save_settings():
    with open(CACHE_DIR + "/settings.json", "w", encoding="utf-8") as f:
        json.dump(fake_settings, f, ensure_ascii=False, indent=2)

def process_incoming_message(client, author_id, message_text, message_object, thread_id, thread_type):
    load_settings()
    
    if not fake_settings.get("enabled", False):
        return
    
    if str(author_id) == str(client.uid):
        return
    
    prefix = client.settings.get("prefix", ".")
    if message_text.startswith(prefix):
        return
    
    should_reply = False
    
    if thread_type == ThreadType.USER:
        should_reply = True
    elif thread_type == ThreadType.GROUP:
        mention_only = fake_settings.get("mention_only", True)
        if not mention_only:
            should_reply = True
        else:
            if message_object.mentions:
                for mention in message_object.mentions:
                    if str(mention.get('uid')) == str(client.uid):
                        should_reply = True
                        break
    
    if not should_reply:
        return
    
    try:
        client.sendTyping(thread_id, thread_type)
    except:
        pass
    
    reply_delay = fake_settings.get("reply_delay", 2)
    time.sleep(reply_delay)
    
    if fake_settings.get("use_random", True):
        reply_text = random.choice(fake_settings.get("random_reply", ["Xin chào!"]))
    else:
        reply_text = fake_settings.get("auto_reply", "Xin chào!")
    
    try:
        client.send(Message(text=reply_text), thread_id=thread_id, thread_type=thread_type, ttl=60000)
        print(f"[Fake] Đã trả lời: {reply_text[:50]}")
    except Exception as e:
        print(f"[Fake] Lỗi: {e}")

def handle_fake_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("fake"):
        return
    
    # Kiểm tra admin tạm thời bỏ qua để test
    # if not is_admin(author_id):
    #     client.replyMessage(Message(text="❌ Bạn không có quyền!"), message_object, thread_id, thread_type, ttl=30000)
    #     return
    
    content = cmd[4:].strip()
    parts = content.split()
    
    load_settings()
    
    if not content:
        help_text = f"""
📢 FAKE - TỰ ĐỘNG TRẢ LỜI

{prefix}fake on        - Bật
{prefix}fake off       - Tắt
{prefix}fake set "nd"  - Đặt nội dung
{prefix}fake delay 2   - Delay 2 giây
{prefix}fake status    - Xem trạng thái

Ví dụ:
{prefix}fake on
{prefix}fake set "Tôi đang bận!"
        """
        client.replyMessage(Message(text=help_text.strip()), message_object, thread_id, thread_type, ttl=60000)
        return
    
    mode = parts[0].lower()
    
    if mode == "on":
        fake_settings["enabled"] = True
        save_settings()
        client.replyMessage(Message(text="✅ ĐÃ BẬT FAKE TYPING"), message_object, thread_id, thread_type, ttl=30000)
    
    elif mode == "off":
        fake_settings["enabled"] = False
        save_settings()
        client.replyMessage(Message(text="🔴 ĐÃ TẮT FAKE TYPING"), message_object, thread_id, thread_type, ttl=30000)
    
    elif mode == "set":
        if len(parts) < 2:
            client.replyMessage(Message(text="❌ .fake set <nội dung>"), message_object, thread_id, thread_type, ttl=30000)
            return
        content_text = " ".join(parts[1:])
        fake_settings["auto_reply"] = content_text
        fake_settings["use_random"] = False
        save_settings()
        client.replyMessage(Message(text=f"✅ Đã đặt: {content_text[:50]}"), message_object, thread_id, thread_type, ttl=30000)
    
    elif mode == "delay":
        if len(parts) < 2:
            client.replyMessage(Message(text="❌ .fake delay <giây>"), message_object, thread_id, thread_type, ttl=30000)
            return
        try:
            delay = float(parts[1].replace(',', '.'))
            fake_settings["reply_delay"] = delay
            save_settings()
            client.replyMessage(Message(text=f"✅ Delay: {delay}s"), message_object, thread_id, thread_type, ttl=30000)
        except:
            client.replyMessage(Message(text="❌ Delay phải là số!"), message_object, thread_id, thread_type, ttl=30000)
    
    elif mode == "status":
        status = "🟢 BẬT" if fake_settings.get("enabled") else "🔴 TẮT"
        msg = f"""
📊 TRẠNG THÁI FAKE
━━━━━━━━━━━━━━━━━━
🔘 Trạng thái: {status}
⏱️ Delay: {fake_settings.get('reply_delay', 2)}s
📝 Nội dung: {fake_settings.get('auto_reply', 'Chưa đặt')[:50]}
        """
        client.replyMessage(Message(text=msg.strip()), message_object, thread_id, thread_type, ttl=60000)
    
    else:
        client.replyMessage(Message(text=f"❌ Lệnh '{mode}' không tồn tại!"), message_object, thread_id, thread_type, ttl=30000)

def LIGHT():
    return {"fake": handle_fake_command}