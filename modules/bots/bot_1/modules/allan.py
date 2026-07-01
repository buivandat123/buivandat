# modules/allan.py
import os
import time
from zlapi.models import Message, Mention, MultiMention

des = {
    'version': "1.0.2",
    'credits': "WJX",
    'description': "All ẩn - tag toàn bộ thành viên"
}

ADMIN = os.environ.get('ADMIN', '').split(',') if os.environ.get('ADMIN') else []
PREFIX = os.environ.get('BOT_PREFIX', '>')

def handle_allan_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        content = message.strip().split(' ', 1)
        if len(content) < 2:
            client.send(Message(text="Nhập nội dung bé ơi"), thread_id=thread_id, thread_type=thread_type)
            return
        
        wjxz = content[1] 
        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        thanhvien = group_info.get('memVerList', [])
        mention = [Mention(userId.split('_')[0], length=3000, offset=0, auto_format=False) for userId in thanhvien]
        wjxz_mention = MultiMention(mention)

        client.send(Message(text=wjxz, mention=wjxz_mention), thread_id=thread_id, thread_type=thread_type)

    except Exception as e:
        error_message = f"Lỗi xảy ra: {str(e)}"
        client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type)

def Kryzis():
    return {
        'cd': handle_allan_command
    }