# modules/lqskin.py
# -*- coding: utf-8 -*-
import os
import re
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "2.0.0",
    "credits": "kryzis X TXA",
    "description": "Tra cứu skin Liên Quân",
    "power": "Thành viên"
}

SKIN_FILE = "modules/Skin ID list_2.txt"

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text):
    client.replyMessage(Message(text=text, style=_sty(text)), msg_obj, tid, ttype)

def load_skin_data():
    skin_data = {}
    current_hero = None
    
    if not os.path.exists(SKIN_FILE):
        return skin_data
    
    with open(SKIN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            hero_match = re.match(r'^([A-Za-zÀ-Ỹ\u1ea0-\u1eff\s\']+)\s*\((\d+)\):$', line)
            if hero_match:
                current_hero = hero_match.group(1).strip()
                hero_id = hero_match.group(2)
                skin_data[current_hero] = {"id": hero_id, "skins": []}
                continue
            
            if current_hero:
                skin_match = re.match(r'\s*([●○])(\d+)\s*-\s*(.+)$', line)
                if skin_match:
                    has_effect = skin_match.group(1) == '●'
                    skin_id = skin_match.group(2)
                    skin_name = skin_match.group(3).strip()
                    skin_data[current_hero]["skins"].append({
                        "id": skin_id,
                        "name": skin_name,
                        "effect": has_effect
                    })
    
    return skin_data

user_states = {}

def handle_skin_choice(message_text, message_object, thread_id, thread_type, author_id, client):
    if author_id not in user_states:
        return False
    
    state = user_states[author_id]
    if time.time() - state['time'] > 300:
        del user_states[author_id]
        return False
    
    if not message_text.isdigit():
        return False
    
    skin_num = int(message_text)
    
    # Chọn tướng từ ds
    if state.get('type') == 'ds':
        heroes = state['heroes']
        skin_data = state['skin_data']
        if 1 <= skin_num <= len(heroes):
            hero_name = heroes[skin_num - 1]
            hero_info = skin_data[hero_name]
            skins = hero_info["skins"]
            
            user_states[author_id] = {
                'hero': hero_name,
                'hero_info': hero_info,
                'time': time.time()
            }
            
            lines = [f"{hero_name} (ID: {hero_info['id']})"]
            for i, skin in enumerate(skins, 1):
                symbol = "●" if skin["effect"] else "○"
                name = skin['name'][:45] + '..' if len(skin['name']) > 45 else skin['name']
                lines.append(f"{i}. {symbol} {skin['id']} - {name}")
            
            _reply(client, message_object, thread_id, thread_type, "\n".join(lines) + f"\n\nReply số 1-{len(skins)}")
            return True
        else:
            _reply(client, message_object, thread_id, thread_type, f"❌ Số {skin_num} không có")
            del user_states[author_id]
            return True
    
    # Chọn skin từ base
    if state.get('hero_info'):
        skins = state['hero_info']['skins']
        if 1 <= skin_num <= len(skins):
            skin = skins[skin_num - 1]
            effect = "Có hiệu ứng" if skin["effect"] else "Không hiệu ứng"
            _reply(client, message_object, thread_id, thread_type, f"{state['hero']}\n{skin['name']}\nID: {skin['id']}\n{effect}")
            del user_states[author_id]
            return True
    
    return False

def handle_ds(message, message_object, thread_id, thread_type, author_id, client):
    skin_data = load_skin_data()
    if not skin_data:
        _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy dữ liệu")
        return
    
    heroes = list(skin_data.keys())
    user_states[author_id] = {
        'type': 'ds',
        'heroes': heroes,
        'skin_data': skin_data,
        'time': time.time()
    }
    
    lines = []
    for i, hero in enumerate(heroes, 1):
        hero_id = skin_data[hero]['id']
        skin_count = len(skin_data[hero]['skins'])
        lines.append(f"{i}. {hero} (ID: {hero_id} - {skin_count} skin)")
    
    _reply(client, message_object, thread_id, thread_type, "\n".join(lines) + "\n\nReply số để xem skin")

def handle_base(message, message_object, thread_id, thread_type, author_id, client):
    skin_data = load_skin_data()
    if not skin_data:
        _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy dữ liệu")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, "base --id <ID tướng>\nbase --name <tên tướng>")
        return
    
    option = parts[1].lower()
    
    if option == "--id" and len(parts) >= 3:
        search_id = parts[2]
        for hero_name, hero_info in skin_data.items():
            if hero_info['id'] == search_id:
                skins = hero_info["skins"]
                user_states[author_id] = {
                    'hero': hero_name,
                    'hero_info': hero_info,
                    'time': time.time()
                }
                lines = [f"{hero_name} (ID: {hero_info['id']})"]
                for i, skin in enumerate(skins, 1):
                    symbol = "●" if skin["effect"] else "○"
                    name = skin['name'][:50] + '..' if len(skin['name']) > 50 else skin['name']
                    lines.append(f"{i}. {symbol} {skin['id']} - {name}")
                _reply(client, message_object, thread_id, thread_type, "\n".join(lines) + f"\n\nReply số 1-{len(skins)}")
                return
        _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy ID: {search_id}")
        return
    
    if option == "--name" and len(parts) >= 3:
        search_name = " ".join(parts[2:]).lower()
        for hero_name, hero_info in skin_data.items():
            if search_name == hero_name.lower():
                skins = hero_info["skins"]
                user_states[author_id] = {
                    'hero': hero_name,
                    'hero_info': hero_info,
                    'time': time.time()
                }
                lines = [f"{hero_name} (ID: {hero_info['id']})"]
                for i, skin in enumerate(skins, 1):
                    symbol = "●" if skin["effect"] else "○"
                    name = skin['name'][:50] + '..' if len(skin['name']) > 50 else skin['name']
                    lines.append(f"{i}. {symbol} {skin['id']} - {name}")
                _reply(client, message_object, thread_id, thread_type, "\n".join(lines) + f"\n\nReply số 1-{len(skins)}")
                return
        _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {search_name}")
        return
    
    _reply(client, message_object, thread_id, thread_type, "base --id <ID>\nbase --name <tên>")

def handle_find(message, message_object, thread_id, thread_type, author_id, client):
    skin_data = load_skin_data()
    if not skin_data:
        _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy dữ liệu")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, "find <tên tướng>")
        return
    
    search_name = " ".join(parts[1:]).lower()
    found = []
    for hero_name, hero_info in skin_data.items():
        if search_name in hero_name.lower():
            found.append((hero_name, hero_info))
    
    if not found:
        _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy: {search_name}")
        return
    
    if len(found) == 1:
        hero_name, hero_info = found[0]
        skins = hero_info["skins"]
        lines = [f"{hero_name} (ID: {hero_info['id']})"]
        for skin in skins:
            symbol = "●" if skin["effect"] else "○"
            name = skin['name'][:50] + '..' if len(skin['name']) > 50 else skin['name']
            lines.append(f"{symbol} {skin['id']} - {name}")
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines))
    else:
        lines = [f"🔍 Tìm thấy {len(found)} tướng:"]
        for hero_name, hero_info in found:
            lines.append(f"{hero_name} (ID: {hero_info['id']} - {len(hero_info['skins'])} skin)")
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines))

def handle_skinid(message, message_object, thread_id, thread_type, author_id, client):
    skin_data = load_skin_data()
    if not skin_data:
        _reply(client, message_object, thread_id, thread_type, "❌ Không tìm thấy dữ liệu")
        return
    
    parts = message.split()
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type, "skinid <số ID skin>")
        return
    
    search_id = parts[1]
    
    for hero_name, hero_info in skin_data.items():
        for skin in hero_info["skins"]:
            if skin['id'] == search_id:
                effect = "Có hiệu ứng" if skin["effect"] else "Không hiệu ứng"
                _reply(client, message_object, thread_id, thread_type, f"{hero_name}\n{skin['name']}\nID: {skin['id']}\n{effect}")
                return
    
    _reply(client, message_object, thread_id, thread_type, f"❌ Không tìm thấy ID: {search_id}")

def LIGHT():
    return {
        "ds": handle_ds,
        "base": handle_base,
        "find": handle_find,
        "skinid": handle_skinid
    }