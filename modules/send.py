import threading
import time
import random
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from asset.config import PREFIX
from asset.admin_check import is_admin

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Gửi tin nhắn hàng loạt",
    'power': "Admin"
}

def style_warning(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#F7B503", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def style_success(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#15A85F", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def style_error(text):
    lines = text.split('\n')
    first_line = lines[0] if lines else ""
    styles = [MessageStyle(offset=0, length=len(text), style="font", size="0", auto_format=False)]
    if first_line:
        first_line_len = len(first_line) + 1
        styles.append(MessageStyle(offset=0, length=first_line_len, style="color", color="#DB342E", auto_format=False))
        styles.append(MessageStyle(offset=0, length=first_line_len, style="bold", auto_format=False))
    return MultiMsgStyle(styles)

def handle_send(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        msg = "ERROR\n    Bạn không có quyền!"
        client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    parts = message.split(maxsplit=2)
    
    if len(parts) < 3:
        msg = f"WARNING\n    {PREFIX}send -all <nội dung>\n    {PREFIX}send <uid> <nội dung>\n    {PREFIX}send <link> <nội dung>"
        client.replyMessage(Message(text=msg, style=style_warning(msg)), message_object, thread_id, thread_type)
        return
    
    target = parts[1]
    msg_content = parts[2]
    
    if target == "-all":
        msg = f"SUCCESS\n    Đang gửi tin nhắn đến tất cả..."
        client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
        
        def send_all():
            success_group = 0
            fail_group = 0
            success_user = 0
            fail_user = 0
            
            group_ids = []
            try:
                groups_data = client.fetchAllGroups()
                if groups_data and hasattr(groups_data, 'gridVerMap') and groups_data.gridVerMap:
                    group_ids = list(groups_data.gridVerMap.keys())
            except:
                pass
            
            friend_ids = []
            try:
                friends_data = client.fetchAllFriends()
                if friends_data:
                    for friend in friends_data:
                        friend_id = friend.userId if hasattr(friend, 'userId') else str(friend)
                        friend_ids.append(friend_id)
            except:
                pass
            
            for group_id in group_ids:
                try:
                    client.sendMessage(Message(text=msg_content), group_id, ThreadType.GROUP)
                    success_group += 1
                    time.sleep(random.uniform(1, 2))
                except:
                    fail_group += 1
            
            for friend_id in friend_ids:
                try:
                    client.sendMessage(Message(text=msg_content), friend_id, ThreadType.USER)
                    success_user += 1
                    time.sleep(random.uniform(1, 2))
                except:
                    fail_user += 1
            
            result_msg = f"SUCCESS\n    Nhóm: {success_group}/{len(group_ids)}\n    Bạn: {success_user}/{len(friend_ids)}"
            client.sendMessage(Message(text=result_msg, style=style_success(result_msg)), thread_id, thread_type)
        
        threading.Thread(target=send_all, daemon=True).start()
        return
    
    if target.startswith("https://zalo.me/g/"):
        try:
            group_info = client.getIDsGroup(target)
            if group_info and 'groupId' in group_info:
                target_id = group_info['groupId']
                client.sendMessage(Message(text=msg_content), target_id, ThreadType.GROUP)
                msg = f"SUCCESS\n    Đã gửi đến nhóm!"
                client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
            else:
                msg = "ERROR\n    Link nhóm không hợp lệ!"
                client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        except Exception as e:
            msg = f"ERROR\n    {str(e)[:50]}"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if target.isdigit():
        try:
            client.sendMessage(Message(text=msg_content), target, ThreadType.USER)
            msg = f"SUCCESS\n    Đã gửi đến UID: {target}"
            client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
        except Exception as e:
            msg = f"ERROR\n    {str(e)[:50]}"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if message_object.mentions:
        user_id = message_object.mentions[0]['uid']
        try:
            client.sendMessage(Message(text=msg_content), user_id, ThreadType.USER)
            msg = f"SUCCESS\n    Đã gửi đến @{message_object.mentions[0].get('displayName', user_id)}"
            client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
        except Exception as e:
            msg = f"ERROR\n    {str(e)[:50]}"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return
    
    if message_object.quote:
        user_id = str(message_object.quote.ownerId)
        try:
            client.sendMessage(Message(text=msg_content), user_id, ThreadType.USER)
            msg = "SUCCESS\n    Đã gửi đến người được reply!"
            client.replyMessage(Message(text=msg, style=style_success(msg)), message_object, thread_id, thread_type)
        except Exception as e:
            msg = f"ERROR\n    {str(e)[:50]}"
            client.replyMessage(Message(text=msg, style=style_error(msg)), message_object, thread_id, thread_type)
        return

def LIGHT():
    return {'send': handle_send}