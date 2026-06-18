import requests
import os
import logging
import json
import re
from zlapi.models import Message, Mention
import datetime

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "war cùng AI:)",
    'power': "Thành viên"
}

gemini_api_key = "AIzaSyCdcXwfWBzg492rooDiIC7XJvaBy7S4JUM"
conversation_states = {}

os.makedirs('data', exist_ok=True)

try:
    with open('data/promt.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    base_prompt = prompts.get('promt', {}).get('base', 'tao là Tuann, trả lời ngắn gọn không quá 100 từ.')
    history_prefix = prompts.get('promt', {}).get('hisprf', 'lịch sử:')
    user_prefix = prompts.get('promt', {}).get('prf', 'user:')
    postfix = prompts.get('promt', {}).get('postfix', 'trả lời toàn bộ và không chửi ai tên "SANG"!')
except FileNotFoundError:
    logging.warning("promt.json không thấy, dùng mặc định")
    base_prompt = 'tao là Tuann, trả lời ngắn gọn không quá 100 từ.'
    history_prefix = 'lịch sử:'
    user_prefix = 'user:'
    postfix = ''
except json.JSONDecodeError:
    logging.error("file promt.json sai format")
    base_prompt = 'tao là Tuann, trả lời ngắn gọn không quá 100 từ.'
    history_prefix = 'lịch sử:'
    user_prefix = 'user:'
    postfix = ''

def get_chat_response(user_question, conversation_state, thread_id, author_id):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
    headers = {'content-type': 'application/json'}

    prompt = base_prompt + "\n"
    if not conversation_state.get('history'):
        conversation_state['history'] = []
    
    if conversation_state['history']:
        prompt += history_prefix + "\n"
        for item in conversation_state['history'][-10:]:
            prompt += f"{item['role']}: {item['text']}\n"

    prompt += f"{user_prefix}{user_question}\n"
    if postfix:
        prompt += postfix + "\n"
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            conversation_state['history'].append({'role': 'user', 'text': user_question})
                            conversation_state['history'].append({'role': 'bot', 'text': part['text']})
                            conversation_states[thread_id] = conversation_state
                            return part['text']
        return "Xin lỗi, tôi không thể trả lời."
        
    except Exception as e:
        logging.error(f"lỗi AI: {e}")
        return f"Lỗi: {str(e)[:100]}"

def handle_chat_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    command_pattern = rf"^{re.escape(prefix)}chatvar\s*"
    question = re.sub(command_pattern, message, "", flags=re.IGNORECASE).strip()
    
    if not question:
        client.replyMessage(
            Message(text=f"@{author_id} sủa? Dùng: {prefix}chatvar <câu hỏi>", 
                   mention=Mention(author_id, length=len("@member"), offset=0)),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    conversation_state = conversation_states.get(thread_id, {'history': [], 'user_id': author_id})
    
    chat_response = get_chat_response(question, conversation_state, thread_id, author_id)
    
    if chat_response:
        client.replyMessage(
            Message(text=f"@{author_id} {chat_response}", 
                   mention=Mention(author_id, length=len("@member"), offset=0)),
            message_object, thread_id, thread_type, ttl=720000
        )
    else:
        client.replyMessage(
            Message(text="đ muốn rep"),
            message_object, thread_id, thread_type, ttl=12000
        )

def LIGHT():
    return {
        'chatvar': handle_chat_command,
        'varchat': handle_chat_command
    }