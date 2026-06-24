# modules/menu.py
# -*- coding: utf-8 -*-
import os
import importlib
from datetime import datetime

from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Hiển thị danh sách lệnh",
    "power": "User"
}

def _sty(text, color="#00BFFF"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _sty_success(text):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="1", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color="#15A85F", auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def _reply(client, msg_obj, tid, ttype, text, sty=None):
    if sty is None:
        sty = _sty
    client.replyMessage(Message(text=text, style=sty(text)), msg_obj, thread_id=tid, thread_type=ttype)

def get_all_commands():
    commands = {}
    modules_dir = "modules"
    
    if not os.path.exists(modules_dir):
        return commands
    
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and filename != '__init__.py' and filename not in ['sleep.py', 'startwith.py']:
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'modules.{module_name}')
                if hasattr(module, 'Kryzis'):
                    light_func = getattr(module, 'Kryzis')
                    if callable(light_func):
                        cmds = light_func()
                        if isinstance(cmds, dict):
                            for cmd_name in cmds.keys():
                                if cmd_name and not cmd_name.isdigit():
                                    commands[cmd_name] = []
            except:
                pass
    
    return dict(sorted(commands.items()))

def handle_menu(message, message_object, thread_id, thread_type, author_id, client):
    from asset.config import PREFIX
    
    commands = get_all_commands()
    
    if not commands:
        _reply(client, message_object, thread_id, thread_type, "❌ Không có lệnh")
        return
    
    lines = ["SUCCESS"]
    for i, cmd in enumerate(commands.keys(), 1):
        lines.append(f"{i}. {cmd}")
    
    menu_text = "\n".join(lines)
    
    if len(menu_text) > 1900:
        mid = len(lines) // 2
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines[:mid]), _sty_success)
        _reply(client, message_object, thread_id, thread_type, "\n".join(lines[mid:]), _sty)
    else:
        _reply(client, message_object, thread_id, thread_type, menu_text, _sty_success)

def Kryzis():
    return {"menu": handle_menu}