import os
import json
import requests
import re
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.0',
    'credits': 'kryzis X TXA',
    'description': 'Trò chuyện với AI (GPT)',
    'power': 'Thành viên'
}

FONT_SIZE = "9"
CACHE_DIR = "modules/cache/gpt"
os.makedirs(CACHE_DIR, exist_ok=True)

conversation_history = {}

def _sty(text, color="#e8eaf6"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=FONT_SIZE, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def ask_gpt(question, conversation_id=None):
    """Gửi câu hỏi đến AI và nhận phản hồi"""
    try:
        # API 1: Blackbox AI (miễn phí, không cần key)
        url = "https://api.blackbox.ai/api/chat"
        payload = {
            "messages": [
                {"id": conversation_id or "1", "role": "user", "content": question}
            ],
            "model": "llama-3.1-8b",
            "max_tokens": 1000
        }
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'message' in data:
                return data['message'], None
            elif 'response' in data:
                return data['response'], None
        
        # API 2: Dự phòng
        url2 = "https://api.gpt4.ai/v1/chat"
        payload2 = {
            "prompt": question,
            "max_tokens": 1000
        }
        response2 = requests.post(url2, json=payload2, timeout=30)
        if response2.status_code == 200:
            return response2.text, None
            
        return None, "Không thể kết nối AI"
        
    except requests.exceptions.Timeout:
        return None, "Yêu cầu bị timeout"
    except Exception as e:
        return None, str(e)

def handle_gpt_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("gpt"):
        return
    
    content = cmd[3:].strip()
    
    # Reset history
    if content.lower() == "reset":
        if author_id in conversation_history:
            del conversation_history[author_id]
        client.replyMessage(
            Message(text="✅ Đã xóa lịch sử trò chuyện!", style=_sty("✅ Đã xóa!", "#15A85F")),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    if not content:
        help_text = f"""
🤖 GPT - TRÒ CHUYỆN VỚI AI

Cách dùng:
{prefix}gpt <câu hỏi>
{prefix}gpt reset - Xóa lịch sử

Ví dụ:
{prefix}gpt Hôm nay thế nào?
{prefix}gpt Python là gì?
{prefix}gpt Kể một câu chuyện

💡 AI sẽ nhớ lịch sử trò chuyện
        """
        client.replyMessage(
            Message(text=help_text.strip(), style=_sty(help_text, "#00BFFF")),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # Thông báo đang xử lý
    client.replyMessage(
        Message(text="🤖 Đang suy nghĩ...", style=_sty("🤖 Đang suy nghĩ...", "#F7B503")),
        message_object, thread_id, thread_type, ttl=10000
    )
    
    # Gọi AI
    answer, error = ask_gpt(content, str(author_id))
    
    if answer:
        # Cắt ngắn nếu quá dài
        if len(answer) > 1500:
            answer = answer[:1500] + "..."
        
        # Lưu lịch sử (đơn giản)
        if author_id not in conversation_history:
            conversation_history[author_id] = []
        conversation_history[author_id].append({"user": content, "bot": answer})
        if len(conversation_history[author_id]) > 10:
            conversation_history[author_id] = conversation_history[author_id][-10:]
        
        client.replyMessage(
            Message(text=f"🤖 {answer}", style=_sty(answer, "#e8eaf6")),
            message_object, thread_id, thread_type, ttl=60000
        )
    else:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {error}", style=_sty(f"❌ Lỗi: {error}", "#DB342E")),
            message_object, thread_id, thread_type, ttl=30000
        )

def Kryzis():
    return {"gpt": handle_gpt_command}