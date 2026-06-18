import requests
import os
import logging
import json
import re
from zlapi.models import Message, Mention

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

des = {
    'version': "2.0.0",
    'credits': "Hoàng Vĩnh Phúc & Yuta Bot",
    'description': "Trò chuyện với AI Gemini",
    'power': "Thành viên"
}

gemini_api_key = "AIzaSyCdcXwfWBzg492rooDiIC7XJvaBy7S4JUM"
conversation_states = {}

# Tạo thư mục data nếu chưa có
os.makedirs('data', exist_ok=True)

# Load prompts
try:
    with open('data/promt.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    base_prompt = prompts.get('promt', {}).get('base', 'Bạn là trợ lý AI thân thiện, trả lời ngắn gọn.')
    history_prefix = prompts.get('promt', {}).get('hisprf', 'Lịch sử:')
    user_prefix = prompts.get('promt', {}).get('prf', 'Người dùng:')
    postfix = prompts.get('promt', {}).get('postfix', '')
except FileNotFoundError:
    logging.warning("promt.json không tìm thấy, sử dụng cài đặt mặc định")
    base_prompt = 'Bạn là trợ lý AI thân thiện, trả lời ngắn gọn.'
    history_prefix = 'Lịch sử:'
    user_prefix = 'Người dùng:'
    postfix = ''
except json.JSONDecodeError:
    logging.error("File promt.json sai format, sử dụng cài đặt mặc định")
    base_prompt = 'Bạn là trợ lý AI thân thiện, trả lời ngắn gọn.'
    history_prefix = 'Lịch sử:'
    user_prefix = 'Người dùng:'
    postfix = ''

def get_chat_response(user_question, conversation_state, thread_id, author_id):
    """Gọi API Gemini để lấy phản hồi"""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
    headers = {'content-type': 'application/json'}

    # Xây dựng prompt
    prompt = base_prompt + "\n"
    
    if conversation_state.get('history'):
        prompt += history_prefix + "\n"
        for item in conversation_state['history'][-10:]:
            prompt += f"{item['role']}: {item['text']}\n"
    
    prompt += f"{user_prefix}{user_question}\n"
    if postfix:
        prompt += postfix + "\n"
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            text = part['text']
                            # Lưu lịch sử
                            conversation_state.setdefault('history', []).append({'role': 'user', 'text': user_question})
                            conversation_state['history'].append({'role': 'assistant', 'text': text})
                            conversation_states[thread_id] = conversation_state
                            return text
        return "Xin lỗi, tôi không thể trả lời câu hỏi này."
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi request Gemini: {e}")
        return f"Lỗi kết nối AI: {str(e)[:100]}"
    except Exception as e:
        logging.error(f"Lỗi Gemini: {e}")
        return "Đã có lỗi xảy ra, vui lòng thử lại sau."

def handle_chat_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh chat với AI"""
    prefix = client.settings.get("prefix", "")
    
    # Loại bỏ prefix và tên lệnh
    command_pattern = rf"^{re.escape(prefix)}chat\s*"
    question = re.sub(command_pattern, "", message, flags=re.IGNORECASE).strip()
    
    if not question:
        help_text = (
            f"🤖 Lệnh CHAT với AI Gemini\n\n"
            f"Cách dùng: {prefix}chat <câu hỏi>\n"
            f"Ví dụ: {prefix}chat Hôm nay thế nào?\n\n"
            f"💡 Mẹo: Dùng {prefix}chat reset để xóa lịch sử hội thoại"
        )
        client.replyMessage(
            Message(text=help_text),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # Reset lịch sử
    if question.lower() in ('reset', 'xóa', 'xoa', 'clear', 'new'):
        if thread_id in conversation_states:
            del conversation_states[thread_id]
        client.replyMessage(
            Message(text="✅ Đã xóa lịch sử hội thoại!"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Lấy hoặc tạo conversation state
    conversation_state = conversation_states.get(thread_id, {'history': [], 'user_id': author_id})
    
    # Gửi thông báo đang xử lý
    client.replyMessage(
        Message(text="🤔 Đang suy nghĩ..."),
        message_object, thread_id, thread_type, ttl=5000
    )
    
    # Lấy phản hồi từ AI
    response = get_chat_response(question, conversation_state, thread_id, author_id)
    
    # Gửi phản hồi
    if len(response) > 1500:
        response = response[:1500] + "..."
    
    # Tạo mention cho người dùng
    mention = Mention(author_id, length=len("@member"), offset=0)
    
    client.replyMessage(
        Message(text=f"🤖 {response}", mention=mention),
        message_object, thread_id, thread_type, ttl=120000
    )

def LIGHT():
    """Hàm export cho LIGHT.py"""
    return {
        'chat': handle_chat_command
    }