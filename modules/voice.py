from zlapi.models import Message
import json
import os
import re
import requests
import time
from gtts import gTTS

des = {
    'version': "2.0.0",
    'credits': "kryzis X TXA",
    'description': "Chuyển đổi văn bản thành tin nhắn thoại",
    'power': "Thành viên"
}

# Tạo thư mục cache
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def convert_text_to_audio(text, lang='vi'):
    """Chuyển text thành file audio"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = f"voice_{int(time.time() * 1000)}.mp3"
        filepath = os.path.join(CACHE_DIR, filename)
        tts.save(filepath)
        return filepath
    except Exception as e:
        print(f"Lỗi tạo voice: {str(e)}")
        return None

def upload_to_host(file_path):
    """Upload file lên host"""
    try:
        with open(file_path, 'rb') as file:
            files = {'files[]': file}
            response = requests.post('https://uguu.se/upload', files=files, timeout=30)
            result = response.json()
            if result.get('success') and result.get('files'):
                return result['files'][0]['url']
    except Exception as e:
        print(f"Lỗi upload: {e}")
    return None

def delete_file(file_path):
    """Xóa file tạm"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

def handle_voice_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh voice - chuyển text thành giọng nói"""
    prefix = client.settings.get("prefix", "")
    
    # Loại bỏ prefix và tên lệnh
    command_pattern = rf"^{re.escape(prefix)}voice\s*"
    text = re.sub(command_pattern, "", message, flags=re.IGNORECASE).strip()
    
    if not text:
        help_text = (
            f"🎤 Lệnh VOICE - Chuyển văn bản thành giọng nói\n\n"
            f"Cách dùng: {prefix}voice <nội dung>\n"
            f"Ví dụ: {prefix}voice Xin chào các bạn!\n\n"
            f"⏱️ Giọng đọc: Tiếng Việt (gTTS)"
        )
        client.replyMessage(
            Message(text=help_text),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # Giới hạn độ dài
    if len(text) > 1000:
        text = text[:997] + "..."
        client.sendMessage(
            Message(text="⚠️ Nội dung quá dài, chỉ đọc 1000 ký tự đầu!"),
            thread_id, thread_type, ttl=5000
        )
    
    # Gửi thông báo
    client.replyMessage(
        Message(text="🎤 Đang tạo giọng nói..."),
        message_object, thread_id, thread_type, ttl=5000
    )
    
    # Tạo voice
    audio_file = convert_text_to_audio(text, 'vi')
    
    if not audio_file:
        client.replyMessage(
            Message(text="❌ Không thể tạo giọng nói, vui lòng thử lại!"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # Upload lên host
    voice_url = upload_to_host(audio_file)
    
    if voice_url:
        file_size = os.path.getsize(audio_file)
        client.sendRemoteVoice(
            voice_url, 
            thread_id=thread_id, 
            thread_type=thread_type, 
            fileSize=file_size,
            ttl=120000
        )
    else:
        client.replyMessage(
            Message(text="❌ Không thể upload file âm thanh!"),
            message_object, thread_id, thread_type, ttl=30000
        )
    
    # Xóa file tạm
    delete_file(audio_file)

def LIGHT():
    """Hàm export cho LIGHT.py"""
    return {
        'voice': handle_voice_command
    }