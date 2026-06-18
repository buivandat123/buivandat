from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from asset.config import PREFIX
from asset.admin_check import is_admin
import json
import os

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Change bot prefix",
    'power': "Admin"
}

def warning_style():
    return MultiMsgStyle([
        MessageStyle(offset=0, length=7, style="bold", auto_format=False),
        MessageStyle(offset=0, length=7, style="color", color="#F7B503", auto_format=False),
        MessageStyle(offset=0, length=100000, style="font", size="0", auto_format=False)
    ])

def success_style(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    
    styles = []
    styles.append(MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False))
    
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#15A85F", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    
    return MultiMsgStyle(styles)

def update_prefix(new_prefix):
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SETTINGS_PATH = os.path.join(BASE_DIR, 'asset', 'seting.json')
        
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        settings['prefix'] = new_prefix
        
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Error updating prefix: {e}")
        return False

def handle_prefix(message, message_object, thread_id, thread_type, author_id, client):
    
    msg_text = message.strip().lower()
    
    if msg_text == "prefix":
        client.replyMessage(
            Message(text=PREFIX, style=success_style(PREFIX)),
            message_object, thread_id, thread_type
        )
        return
    
    parts = message.split()
    
    if len(parts) >= 2 and parts[1] == "-new":
        if not is_admin(author_id):
            client.replyMessage(
                Message(text="WARNING\n    You don't have permission!", style=warning_style()),
                message_object, thread_id, thread_type
            )
            return
        
        if len(parts) < 3:
            client.replyMessage(
                Message(text=f"WARNING\n    Usage: {PREFIX}prefix -new <new_prefix>", style=warning_style()),
                message_object, thread_id, thread_type
            )
            return
        
        new_prefix = parts[2]
        
        if len(new_prefix) > 5:
            client.replyMessage(
                Message(text="WARNING\n    Prefix too long! Max 5 characters.", style=warning_style()),
                message_object, thread_id, thread_type
            )
            return
        
        if update_prefix(new_prefix):
            info_msg = f"""
PREFIX
    Changed successfully!
    Old: {PREFIX}
    New: {new_prefix}
    
    Type {new_prefix}reload to apply.
"""
            client.replyMessage(
                Message(text=info_msg, style=success_style(info_msg)),
                message_object, thread_id, thread_type
            )
        else:
            client.replyMessage(
                Message(text="WARNING\n    Failed to change prefix!", style=warning_style()),
                message_object, thread_id, thread_type
            )
        return

def LIGHT():
    return {'prefix': handle_prefix}