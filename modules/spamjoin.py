import os
import json
import time
import threading
import random
from zlapi.models import Message, ThreadType

des = {
    'version': '1.0.0',
    'credits': 'kryzis X TXA',
    'description': 'Spam join/leave nhóm tự động',
    'power': 'Admin'
}

CACHE_DIR = "modules/cache/spj"
os.makedirs(CACHE_DIR, exist_ok=True)

spj_tasks = {}

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

def save_group_link(link, author_id):
    data = _load_json(CACHE_DIR + "/links.json", [])
    data.append({
        "link": link,
        "author": author_id,
        "time": time.time()
    })
    _save_json(CACHE_DIR + "/links.json", data)

def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def spj_worker(client, group_link, delay, stop_event, task_id, thread_id, thread_type):
    """Worker spam join/leave"""
    count = 0
    imei = client._state.user_imei if hasattr(client, '_state') else ""
    
    try:
        client.send(Message(text=f"🚀 BẮT ĐẦU SPAM JOIN: {group_link[:50]}"), thread_id=thread_id, thread_type=thread_type, ttl=10000)
    except:
        pass
    
    while not stop_event.is_set():
        try:
            print(f"[SPJ] Lần {count+1}: Đang join {group_link}")
            
            # Join nhóm
            result = client.joinGroup(group_link)
            print(f"[SPJ] Join result: {result}")
            
            time.sleep(1)
            
            # Lấy group_id
            group_id = None
            if result and isinstance(result, dict):
                group_id = result.get('groupId')
            
            if not group_id:
                try:
                    info = client.getIDsGroup(group_link)
                    if info and 'groupId' in info:
                        group_id = info['groupId']
                except:
                    pass
            
            # Leave nhóm - THÊM IMEI
            if group_id:
                print(f"[SPJ] Đang leave {group_id}")
                client.leaveGroup(group_id, imei=imei)
                print(f"[SPJ] Leave thành công {group_id}")
            
            count += 1
            print(f"[SPJ] Đã thực hiện {count} lần")
            
            # Delay
            time.sleep(delay)
            
        except Exception as e:
            print(f"[SPJ] Lỗi: {e}")
            time.sleep(delay)
    
    if task_id in spj_tasks:
        del spj_tasks[task_id]
    
    try:
        client.send(Message(text=f"🛑 ĐÃ DỪNG SPAM JOIN\nĐã thực hiện: {count} lần"), thread_id=thread_id, thread_type=thread_type, ttl=30000)
    except:
        pass
    
    print(f"[SPJ] Dừng, đã thực hiện {count} lần")

def spj_multiple_worker(client, links, delay, stop_event, task_id, thread_id, thread_type):
    """Worker spam join nhiều nhóm"""
    count = 0
    idx = 0
    total = len(links)
    imei = client._state.user_imei if hasattr(client, '_state') else ""
    
    try:
        client.send(Message(text=f"🚀 BẮT ĐẦU SPAM JOIN {total} NHÓM"), thread_id=thread_id, thread_type=thread_type, ttl=10000)
    except:
        pass
    
    while not stop_event.is_set():
        try:
            link = links[idx % total]
            print(f"[SPJ] Lần {count+1}: Đang join {link[:50]}")
            
            result = client.joinGroup(link)
            print(f"[SPJ] Join result: {result}")
            time.sleep(1)
            
            group_id = None
            if result and isinstance(result, dict):
                group_id = result.get('groupId')
            
            if not group_id:
                try:
                    info = client.getIDsGroup(link)
                    if info and 'groupId' in info:
                        group_id = info['groupId']
                except:
                    pass
            
            if group_id:
                print(f"[SPJ] Đang leave {group_id}")
                client.leaveGroup(group_id, imei=imei)
                print(f"[SPJ] Leave thành công {group_id}")
            
            count += 1
            idx += 1
            print(f"[SPJ] Đã thực hiện {count} lần")
            
            time.sleep(delay)
            
        except Exception as e:
            print(f"[SPJ] Lỗi: {e}")
            time.sleep(delay)
    
    if task_id in spj_tasks:
        del spj_tasks[task_id]
    
    try:
        client.send(Message(text=f"🛑 ĐÃ DỪNG SPAM JOIN\nĐã thực hiện: {count} lần"), thread_id=thread_id, thread_type=thread_type, ttl=30000)
    except:
        pass
    
    print(f"[SPJ] Dừng, đã thực hiện {count} lần")

def handle_spj_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if not cmd.startswith("spj"):
        return
    
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền!"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    content = cmd[3:].strip()
    parts = content.split()
    
    # STOP
    if content.lower() == "stop":
        task_id = str(thread_id)
        if task_id in spj_tasks:
            spj_tasks[task_id].set()
            client.replyMessage(
                Message(text="✅ Đã dừng spam join!"),
                message_object, thread_id, thread_type, ttl=30000
            )
        else:
            client.replyMessage(
                Message(text="❌ Không có spam nào đang chạy!"),
                message_object, thread_id, thread_type, ttl=30000
            )
        return
    
    # LIST LINK
    if content.lower() == "list":
        links = _load_json(CACHE_DIR + "/links.json", [])
        if not links:
            client.replyMessage(
                Message(text="📭 Chưa có link nào được lưu!\nDùng: .spj save <link>"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        lines = ["📋 DANH SÁCH LINK NHÓM", "━━━━━━━━━━━━━━━━━━━━━━"]
        for i, l in enumerate(links[-15:], 1):
            lines.append(f"{i}. {l['link'][:60]}")
        client.replyMessage(
            Message(text="\n".join(lines)),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # SAVE LINK
    if content.lower().startswith("save"):
        link_parts = content.split()
        if len(link_parts) < 2:
            client.replyMessage(
                Message(text="❌ .spj save <link_nhóm>"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        link = link_parts[1]
        save_group_link(link, author_id)
        client.replyMessage(
            Message(text=f"✅ Đã lưu link: {link[:60]}"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # CLEAR LINK
    if content.lower() == "clear":
        _save_json(CACHE_DIR + "/links.json", [])
        client.replyMessage(
            Message(text="✅ Đã xóa toàn bộ link!"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # HELP
    if not parts:
        help_text = f"""
╔══════════════════════════════════════════════════════════╗
║              📢 SPJ - SPAM JOIN NHÓM                    ║
╠══════════════════════════════════════════════════════════╣
║  {prefix}spj <link> <delay>                             ║
║  {prefix}spj all <delay>                                ║
║  {prefix}spj save <link>                                ║
║  {prefix}spj list                                       ║
║  {prefix}spj clear                                      ║
║  {prefix}spj stop                                       ║
╠══════════════════════════════════════════════════════════╣
║  💡 Ví dụ:                                               ║
║  {prefix}spj https://zalo.me/g/xxx 3                    ║
║  {prefix}spj all 5                                      ║
║  {prefix}spj save https://zalo.me/g/xxx                 ║
║  {prefix}spj list                                       ║
║  {prefix}spj stop                                       ║
╚══════════════════════════════════════════════════════════╝
        """
        client.replyMessage(
            Message(text=help_text.strip()),
            message_object, thread_id, thread_type, ttl=60000
        )
        return
    
    # SPJ 1 LINK
    if len(parts) >= 2 and parts[0].startswith("https://zalo.me/g/"):
        group_link = parts[0]
        delay = float(parts[1].replace(',', '.')) if len(parts) > 1 else 3
        
        task_id = str(thread_id)
        if task_id in spj_tasks:
            client.replyMessage(
                Message(text="⚠️ Đang có spam chạy! Dùng .spj stop trước."),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        stop_event = threading.Event()
        spj_tasks[task_id] = stop_event
        
        thread = threading.Thread(
            target=spj_worker,
            args=(client, group_link, delay, stop_event, task_id, thread_id, thread_type),
            daemon=True
        )
        thread.start()
        
        client.replyMessage(
            Message(text=f"✅ ĐÃ BẮT ĐẦU SPAM JOIN\n🔗 {group_link[:60]}\n⏱️ Delay: {delay}s"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    # SPJ ALL
    if parts[0].lower() == "all":
        delay = float(parts[1].replace(',', '.')) if len(parts) > 1 else 5
        
        links = _load_json(CACHE_DIR + "/links.json", [])
        if not links:
            client.replyMessage(
                Message(text="❌ Chưa có link nào được lưu!\nDùng: .spj save <link>"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        link_list = [l['link'] for l in links]
        
        task_id = str(thread_id)
        if task_id in spj_tasks:
            client.replyMessage(
                Message(text="⚠️ Đang có spam chạy! Dùng .spj stop trước."),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        stop_event = threading.Event()
        spj_tasks[task_id] = stop_event
        
        thread = threading.Thread(
            target=spj_multiple_worker,
            args=(client, link_list, delay, stop_event, task_id, thread_id, thread_type),
            daemon=True
        )
        thread.start()
        
        client.replyMessage(
            Message(text=f"✅ ĐÃ BẮT ĐẦU SPAM JOIN {len(link_list)} NHÓM\n⏱️ Delay: {delay}s"),
            message_object, thread_id, thread_type, ttl=30000
        )
        return
    
    client.replyMessage(
        Message(text="❌ Link không hợp lệ!\nVD: .spj https://zalo.me/g/xxx 3"),
        message_object, thread_id, thread_type, ttl=30000
    )

def LIGHT():
    return {"spj": handle_spj_command}