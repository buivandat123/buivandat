# modules/bots/bot_1/bot.py
import os
import sys
import json
import time
import importlib
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType

try:
    from asset.config import API_KEY, SECRET_KEY
except:
    API_KEY = "api_key"
    SECRET_KEY = "secret_key"

class Bot(ZaloAPI):
    def __init__(self, bot_id, imei, session_cookies, prefix, modules_dir, admin_id):
        self._imei = imei
        self.imei = imei
        self.bot_id = bot_id
        self.prefix = prefix
        self.admin_id = admin_id  # Lưu admin ID
        self._running = True
        self.modules_dir = modules_dir
        self.commands = {}
        
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        
        try:
            super().__init__(API_KEY, SECRET_KEY, imei, session_cookies)
        except Exception as e:
            if "Phone and password not set" in str(e):
                print(f"[bot_1] ⚠️ Login skipped, using session cookies")
            else:
                print(f"[bot_1] Init error: {e}")
                raise
        
        self._imei = imei
        self.imei = imei
        
        self.load_commands()
        print(f"[bot_1] Bot initialized with prefix: ,")
        print(f"[bot_1] Admin ID: {admin_id}")
    
    def load_commands(self):
        try:
            from modules.mybot import Kryzis
            cmds = Kryzis()
            if isinstance(cmds, dict):
                for name, handler in cmds.items():
                    self.commands[name] = {
                        "name": name,
                        "main": handler,
                        "permission": 0,
                        "description": "",
                        "cooldown": 0,
                        "status": True,
                        "alias": []
                    }
                    print(f"[bot_1] ✅ Loaded: {name}")
        except Exception as e:
            print(f"[bot_1] ⚠️ Load mybot error: {e}")
        
        # Load commands from modules
        modules_path = os.path.join(self.modules_dir)
        if os.path.exists(modules_path):
            for filename in os.listdir(modules_path):
                if filename.endswith('.py') and not filename.startswith('__'):
                    mod_name = filename[:-3]
                    if mod_name == "mybot":
                        continue
                    try:
                        module = importlib.import_module(f"modules.{mod_name}")
                        if hasattr(module, 'Kryzis'):
                            cmds = module.Kryzis()
                            if isinstance(cmds, dict):
                                for name, handler in cmds.items():
                                    self.commands[name] = {
                                        "name": name,
                                        "main": handler,
                                        "permission": 0,
                                        "description": "",
                                        "cooldown": 0,
                                        "status": True,
                                        "alias": []
                                    }
                                    print(f"[bot_1] ✅ Loaded: {name}")
                    except Exception as e:
                        print(f"[bot_1] ⚠️ Load {mod_name} error: {e}")
        
        print(f"[bot_1] 📋 Total commands: {len(self.commands)}")
    
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            if message_object.msgType == "chat.sticker":
                return
            c = message_object.content
            if isinstance(c, dict) and "title" in c:
                msg_text = c["title"]
            elif isinstance(c, str):
                msg_text = c
            else:
                return
            
            if not msg_text or not msg_text.strip():
                return
            
            if not msg_text.startswith(self.prefix):
                return
            
            parts = msg_text[len(self.prefix):].strip().split()
            if not parts:
                return
            
            cmd = parts[0].lower()
            
            if cmd in self.commands:
                handler = self.commands[cmd]["main"]
                handler(msg_text, message_object, thread_id, thread_type, author_id, self)
            else:
                self.sendMessage(Message(text=f"❌ Lệnh {cmd} không tồn tại!"), thread_id, thread_type)
            
        except Exception as e:
            print(f"[bot_1] Error: {e}")
    
    def listen(self):
        print(f"[bot_1] 🤖 Bot listening with prefix: {self.prefix}")
        print(f"[bot_1] 📋 Commands: {list(self.commands.keys())}")
        try:
            super().listen()
        except KeyboardInterrupt:
            print(f"[bot_1] 🛑 Bot stopped")
    
    def run(self):
        self.listen()
    
    def stop(self):
        self._running = False
        if hasattr(self, "stopListening"):
            self.stopListening()
    
    def sendMWarning(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"⚠️ {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def sendMFailed(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"❌ {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def sendMSuccess(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"✅ {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def sendMCustom(self, title, icon, text, userId, threadId, type):
        self.sendMessage(Message(text=f"{icon} {title}: {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
        return None
    
    def sendMention(self, text, userId, threadId, type):
        self.sendMessage(Message(text=f"@{userId} {text}"), threadId, ThreadType.GROUP if type == "group" else ThreadType.USER)
    
    def is_admin(self, user_id):
        """Kiểm tra user có phải admin của bot không"""
        return str(user_id) == str(self.admin_id)
