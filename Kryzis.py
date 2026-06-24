import os
import json
import importlib
import sys
import time
import threading
import re
import random
import difflib
from concurrent.futures import ThreadPoolExecutor
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from zlapi.logging import Logging
from colorama import Fore

sys.path.extend([
    os.path.dirname(os.path.abspath(__file__)),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules/auto'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'modules/noprefix')
])
logger = Logging()

CACHE_DIR = 'modules/cache'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'asset', 'seting.json')
DUYETBOX_FILE = os.path.join(CACHE_DIR, 'duyetboxdata.json')
DISABLED_THREADS_FILE = os.path.join(CACHE_DIR, 'disabled_threads.json')
COOLDOWN_FILE = os.path.join(CACHE_DIR, 'cooldown_settings.json')
STW_CMDS_FILE = os.path.join(CACHE_DIR, 'list_cmd_stw.json') 
MODULES_DIR = 'modules'
NOPREFIX_MODULES_DIR = 'modules/noprefix'
AUTO_MODULES_DIR = 'modules/auto'

# Auto delete settings
AUTO_DELETE_CONFIG_FILE = os.path.join(CACHE_DIR, 'auto_delete_config.json')
DEFAULT_DELETE_DELAY = 10

def load_auto_delete_config():
    try:
        with open(AUTO_DELETE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"delay": DEFAULT_DELETE_DELAY, "enabled": True}

def save_auto_delete_config(config):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(AUTO_DELETE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def get_delete_delay():
    config = load_auto_delete_config()
    return config.get("delay", DEFAULT_DELETE_DELAY) if config.get("enabled", True) else 0

def schedule_delete(client, msg_id, thread_id, thread_type):
    delay = get_delete_delay()
    if delay <= 0:
        return
    def delete():
        time.sleep(delay)
        try:
            client.undoMessage(msgId=msg_id, cliMsgId=str(int(time.time() * 1000)), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
    threading.Thread(target=delete, daemon=True).start()

def load_json(file_path, default=None):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {} if file_path.endswith(".json") else []

def save_json(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def load_duyetbox_data():
    return load_json(DUYETBOX_FILE, [])

def load_disabled_threads():
    return load_json(DISABLED_THREADS_FILE, [])

def save_disabled_threads(disabled_threads):
    save_json(DISABLED_THREADS_FILE, disabled_threads)

def load_stw_commands():
    return load_json(STW_CMDS_FILE, {}).get('commands', [])

def save_stw_commands(commands):
    save_json(STW_CMDS_FILE, {'commands': commands})

def update_any_string(old_string, new_string):
    replaced_count = 0
    files_changed = 0
    pattern = re.compile(re.escape(old_string), re.IGNORECASE)
    for root, dirs, files in os.walk('.'):
        for filename in files:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    new_code, n = pattern.subn(new_string, code)
                    if n > 0:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_code)
                        replaced_count += n
                        files_changed += 1
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý {file_path}: {e}")
    return replaced_count, files_changed

def check_is_admin(author_id):
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            owner = str(data.get("admin", ""))
            admins = [str(x) for x in data.get("adm", [])]
            author_id_str = str(author_id)
            if author_id_str == owner:
                return True
            return author_id_str in admins
    except:
        return False

class ThreadSafeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.RLock()
    def __getitem__(self, key):
        with self.lock:
            return super().__getitem__(key)
    def __setitem__(self, key, value):
        with self.lock:
            super().__setitem__(key, value)
    def get(self, key, default=None):
        with self.lock:
            return super().get(key, default)
    def update(self, *args, **kwargs):
        with self.lock:
            super().update(*args, **kwargs)
    def pop(self, key, default=None):
        with self.lock:
            return super().pop(key, default)
    def __contains__(self, item):
        with self.lock:
            return super().__contains__(item)
    def keys(self):
        with self.lock:
            return list(super().keys())
    def values(self):
        with self.lock:
            return list(super().values())
    def items(self):
        with self.lock:
            return list(super().items())

executor = ThreadPoolExecutor(max_workers=10)

class CommandHandler:
    def __init__(self, client):
        self.client = client
        self.Kryzis = ThreadSafeDict(self._load_modules(MODULES_DIR, 'Kryzis', ['version', 'credits', 'description', 'power']))
        self.noprefix_Kryzis = ThreadSafeDict(self._load_modules(NOPREFIX_MODULES_DIR, 'Kryzis', ['version', 'credits', 'description']))
        self.auto_Kryzis = ThreadSafeDict(self._load_auto_modules())
        self.disabled_threads = ThreadSafeDict({t: True for t in load_disabled_threads()})

        self._admin_id = [self.client.ADMIN] + self.client.ADM if hasattr(self.client, 'ADM') else [self.client.ADMIN]
        self.current_prefix = self.client.settings.get("prefix") or ""

        self.cooldown_settings = load_json(COOLDOWN_FILE, {})
        self.stw_commands = load_stw_commands() 
        self.last_used = ThreadSafeDict()
        self.cooldown_lock = threading.Lock()
        
        logger.info(f"🛡 Prefix hiện tại của bot là '{self.current_prefix}'" 
                         if self.current_prefix else "❌️ Prefix hiện tại của bot là 'no prefix'")
        self._log_commands("start with", self.stw_commands) 
        self.prefix_handlers = self._create_prefix_handlers()

    def _create_prefix_handlers(self):
        return sorted([(self.current_prefix + command, handler)
                       for command, handler in self.Kryzis.items() if self.current_prefix],
                      key=lambda item: len(item[0]), reverse=True)

    def _update_prefix(self):
        new_prefix = self.client.settings.get("prefix") or ""
        if new_prefix != self.current_prefix:
            self.current_prefix = new_prefix
            logger.info(f"🕹 Prefix đã được cập nhật thành '{self.current_prefix}'" 
                             if self.current_prefix else "🎑 Prefix đã được cập nhật thành 'no prefix'")
            self.prefix_handlers = self._create_prefix_handlers()

    def _log_commands(self, command_type, commands):
        if isinstance(commands, dict):
            if commands:
                logger.success(f"Đã load thành công các {command_type}")
            else:
                logger.success(f"Không có {command_type} nào.")
        elif isinstance(commands, list):
            if commands:
                logger.success(f"Đã load thành công các lệnh {command_type}")
            else:
                logger.success(f"Không có lệnh {command_type} nào.")

    def get_username(self, user_id):
        try:
            info = self.client.fetchUserInfo(user_id)
            if info and hasattr(info, "changed_profiles"):
                return info.changed_profiles.get(str(user_id), {}).get('zaloName', 'Không xác định')
            return "Không xác định"
        except Exception:
            return "Không xác định"

    def send_message_async(self, error_message, thread_id, thread_type, author_id):
        executor.submit(self._send_message_blocking, error_message, thread_id, thread_type, author_id)

    def _send_message_blocking(self, error_message, thread_id, thread_type, author_id):
        msg = f"➜{error_message}"
        result = self.client.send(Message(text=msg), thread_id, thread_type, ttl=12000)
        if result and hasattr(result, 'msgId'):
            schedule_delete(self.client, result.msgId, thread_id, thread_type)

    def reply_message_async(self, error_message, message_object, thread_id, thread_type, author_id, style=None, auto_delete=True):
        executor.submit(self._reply_message_blocking, error_message, message_object, thread_id, thread_type, author_id, style, auto_delete)

    def _reply_message_blocking(self, error_message, message_object, thread_id, thread_type, author_id, style=None, auto_delete=True):
        msg = error_message if style else f"➜{error_message}"
        result = self.client.replyMessage(Message(text=msg, style=style), message_object, thread_id=thread_id, thread_type=thread_type, ttl=12000)
        if auto_delete and result and hasattr(result, 'msgId'):
            schedule_delete(self.client, result.msgId, thread_id, thread_type)

    def _load_modules(self, module_path, attribute_name, required_keys):
        modules, success_modules, failed_modules = {}, [], []
        for filename in os.listdir(module_path):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'{module_path.replace("/",".")}.{module_name}')
                    if (hasattr(module, attribute_name) and hasattr(module, 'des') and
                        all(key in module.des for key in required_keys)):
                        modules.update(getattr(module, attribute_name)())
                        success_modules.append(module_name)
                    else:
                        failed_modules.append(module_name)
                except Exception as e:
                    logger.error(f"Không thể load được lệnh '{module_name}' trong {module_path}: {e}")
                    failed_modules.append(module_name)
        if success_modules:
            logger.success(f"Đã load thành công {len(success_modules)} lệnh trong {module_path}")
        if failed_modules:
            logger.warning(f"Không thể load được {len(failed_modules)} lệnh trong {module_path}: {', '.join(failed_modules)}")
        return modules

    def _load_auto_modules(self):
        auto_modules, success_auto, failed_auto = {}, [], []
        for filename in os.listdir(AUTO_MODULES_DIR):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'modules.auto.{module_name}')
                    if hasattr(module, 'start_auto'):
                        auto_modules[module_name] = module
                        success_auto.append(module_name)
                    else:
                        failed_auto.append(module_name)
                except Exception as e:
                    logger.error(f"Không thể load được lệnh auto '{module_name}': {e}")
                    failed_auto.append(module_name)
        if success_auto:
            logger.success(f"Đã load thành công {len(success_auto)} lệnh auto")
            for module in success_auto:
                executor.submit(auto_modules[module].start_auto, self.client)
        if failed_auto:
            logger.warning(f"Không thể load {len(failed_auto)} lệnh auto: {', '.join(failed_auto)}")
        return auto_modules

    def predict_command(self, wrong_command):
        possible_commands = list(self.Kryzis.keys())
        matches = difflib.get_close_matches(wrong_command, possible_commands, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def _handle_cooldown(self, message, message_object, thread_id, thread_type, author_id):
        if not check_is_admin(author_id):
            self.reply_message_async("Bạn không có quyền quản lý cooldown.", message_object, thread_id, thread_type, author_id)
            return
        parts = message.split(self.current_prefix + 'cooldown', 1)
        if len(parts) < 2:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}cooldown [set|remove|list] <command> <time>\nVí dụ: {self.current_prefix}cooldown set menu 3s", message_object, thread_id, thread_type, author_id)
            return
        command_part = parts[1].strip().lower()
        args = command_part.split()
        if not args:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}cooldown [set|remove|list] <command> <time>\nVí dụ: {self.current_prefix}cooldown set menu 3s", message_object, thread_id, thread_type, author_id)
            return
        action = args[0]
        if action == 'set':
            if len(args) < 3:
                self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}cooldown set <command> <time>\nVí dụ: {self.current_prefix}cooldown set menu 3s", message_object, thread_id, thread_type, author_id)
                return
            command, time_str = args[1], args[2]
            is_valid_command = command in self.Kryzis or command in self.stw_commands
            if not is_valid_command:
                self.reply_message_async(f"Lệnh {command} không tồn tại.", message_object, thread_id, thread_type, author_id)
                return
            try:
                if time_str.endswith('s'):
                    cooldown_time = float(time_str[:-1])
                elif time_str.endswith('m'):
                    cooldown_time = float(time_str[:-1]) * 60
                else:
                    cooldown_time = float(time_str)
            except ValueError:
                self.reply_message_async("Thời gian không hợp lệ. Vui lòng sử dụng định dạng số giây (3s) hoặc phút (1m).", message_object, thread_id, thread_type, author_id)
                return
            self.cooldown_settings[command] = cooldown_time
            save_json(COOLDOWN_FILE, self.cooldown_settings)
            self.reply_message_async(f"Đã đặt cooldown {cooldown_time} giây cho lệnh {command}.", message_object, thread_id, thread_type, author_id)
        elif action == 'remove':
            if len(args) < 2:
                self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}cooldown remove <command>", message_object, thread_id, thread_type, author_id)
                return
            command = args[1]
            if command not in self.cooldown_settings:
                self.reply_message_async(f"Lệnh {command} không có cooldown.", message_object, thread_id, thread_type, author_id)
                return
            del self.cooldown_settings[command]
            save_json(COOLDOWN_FILE, self.cooldown_settings)
            self.reply_message_async(f"Đã xóa cooldown của lệnh {command}.", message_object, thread_id, thread_type, author_id)
        elif action == 'list':
            if self.cooldown_settings:
                response = "Danh sách lệnh có cooldown:\n"
                for command, cooldown_time in self.cooldown_settings.items():
                    response += f"- {command}: {cooldown_time} giây\n"
                self.reply_message_async(response.strip(), message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async("Không có lệnh nào được đặt cooldown.", message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}cooldown [set|remove|list] <command> <time>", message_object, thread_id, thread_type, author_id)

    def _handle_credit(self, message, message_object, thread_id, thread_type, author_id):
        if not check_is_admin(author_id):
            self.reply_message_async("Bạn không có quyền sử dụng lệnh credit.", message_object, thread_id, thread_type, author_id)
            return
        parts = message.split(self.current_prefix + 'credit', 1)
        if len(parts) < 2 or not parts[1].strip():
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}credit <chuỗi cũ> - <chuỗi mới>", message_object, thread_id, thread_type, author_id)
            return
        args = parts[1].strip().split('-', 1)
        if len(args) < 2:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}credit <chuỗi cũ> - <chuỗi mới>", message_object, thread_id, thread_type, author_id)
            return
        old_string = args[0].strip()
        new_string = args[1].strip()
        if not old_string or not new_string:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}credit <chuỗi cũ> - <chuỗi mới>", message_object, thread_id, thread_type, author_id)
            return
        replaced_count, files_changed = update_any_string(old_string, new_string)
        if files_changed > 0:
            self.reply_message_async(f"Đã thay thế tất cả '{old_string}' thành '{new_string}' trong {files_changed} file, tổng {replaced_count} lần thay thế.", message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(f"Không tìm thấy chuỗi '{old_string}' trong mã nguồn.", message_object, thread_id, thread_type, author_id)

    def _handle_stw(self, message, message_object, thread_id, thread_type, author_id):
        if not check_is_admin(author_id):
            self.reply_message_async("Bạn không có quyền quản lý lệnh startwith (stw).", message_object, thread_id, thread_type, author_id)
            return
        
        parts = message.split(self.current_prefix + 'stw', 1)
        if len(parts) < 2:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}stw [add|del|list] [command]", message_object, thread_id, thread_type, author_id)
            return
        command_part = parts[1].strip().lower()
        action, *target_parts = command_part.split(' ', 1)
        target = target_parts[0].strip() if target_parts else None

        if action == 'add':
            if not target:
                self.reply_message_async(f"Vui lòng cung cấp tên lệnh để thêm vào danh sách stw.", message_object, thread_id, thread_type, author_id)
                return
            if target not in self.Kryzis:
                self.reply_message_async(f"Lệnh '{target}' không tồn tại trong danh sách lệnh chính.", message_object, thread_id, thread_type, author_id)
                return
            if target not in self.stw_commands:
                self.stw_commands.append(target)
                save_stw_commands(self.stw_commands)
                self._log_commands("start with", self.stw_commands)
                self.reply_message_async(f"Đã thêm lệnh '{target}' vào danh sách start with.", message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async(f"Lệnh '{target}' đã có trong danh sách start with.", message_object, thread_id, thread_type, author_id)
        elif action == 'del':
            if not target:
                self.reply_message_async(f"Vui lòng cung cấp tên lệnh để xóa khỏi danh sách stw.", message_object, thread_id, thread_type, author_id)
                return
            if target in self.stw_commands:
                self.stw_commands.remove(target)
                save_stw_commands(self.stw_commands)
                self._log_commands("start with", self.stw_commands)
                self.reply_message_async(f"Đã xóa lệnh '{target}' khỏi danh sách start with.", message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async(f"Không tìm thấy lệnh '{target}' trong danh sách start with.", message_object, thread_id, thread_type, author_id)
        elif action == 'list':
            if self.stw_commands:
                self.reply_message_async(f"Các lệnh start with: {', '.join(self.stw_commands)}", message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async("Không có lệnh start with nào.", message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}stw [add|del|list] [command]", message_object, thread_id, thread_type, author_id)

    def _check_cooldown(self, command, author_id, thread_id):
        if command not in self.cooldown_settings:
            return True
        cooldown_time = self.cooldown_settings[command]
        key = f"{command}_{author_id}_{thread_id}"
        with self.cooldown_lock:
            current_time = time.time()
            last_used_time = self.last_used.get(key, 0)
            if current_time - last_used_time < cooldown_time:
                remaining = cooldown_time - (current_time - last_used_time)
                return f"Vui lòng chờ {remaining:.1f} giây để sử dụng lại lệnh này."
            self.last_used[key] = current_time
            return True

    def _get_content_message(self, message_object):
        if message_object.msgType == 'chat.sticker':
            return ""
        content = message_object.content
        if isinstance(content, dict) and 'title' in content:
            return content['title']
        elif isinstance(content, str):
            return content
        elif isinstance(content, dict) and 'href' in content:
            return content['href']
        else:
            return ""

    def _execute_command(self, command_handler, message_text, message_object, thread_id, thread_type, author_id, command_name):
        try:
            cooldown_check = self._check_cooldown(command_name, author_id, thread_id)
            if isinstance(cooldown_check, str):
                self.reply_message_async(cooldown_check, message_object, thread_id, thread_type, author_id)
                return
            command_handler(message_text, message_object, thread_id, thread_type, author_id, self.client)
        except Exception as e:
            self.reply_message_async(f"Lỗi khi thực hiện lệnh: {e}", message_object, thread_id, thread_type, author_id)

    def _handle_autodel(self, message, message_object, thread_id, thread_type, author_id):
        if not check_is_admin(author_id):
            self.reply_message_async("❌ Chỉ admin mới dùng được!", message_object, thread_id, thread_type, author_id)
            return
        
        parts = message.split()
        if len(parts) < 2:
            config = load_auto_delete_config()
            delay = config.get("delay", DEFAULT_DELETE_DELAY)
            enabled = config.get("enabled", True)
            status = "🟢 BẬT" if enabled else "🔴 TẮT"
            self.reply_message_async(f"⚙️ TỰ ĐỘNG THU HỒI\n📊 Trạng thái: {status}\n⏱️ Thời gian: {delay} giây\n\n{self.current_prefix}autodel on - Bật\n{self.current_prefix}autodel off - Tắt\n{self.current_prefix}autodel <số> - Đặt thời gian", message_object, thread_id, thread_type, author_id)
            return
        
        arg = parts[1].lower()
        
        if arg == "on":
            config = load_auto_delete_config()
            config["enabled"] = True
            save_auto_delete_config(config)
            self.reply_message_async(f"✅ Đã bật tự động thu hồi tin nhắn bot", message_object, thread_id, thread_type, author_id)
        elif arg == "off":
            config = load_auto_delete_config()
            config["enabled"] = False
            save_auto_delete_config(config)
            self.reply_message_async(f"✅ Đã tắt tự động thu hồi tin nhắn bot", message_object, thread_id, thread_type, author_id)
        elif arg.isdigit():
            delay = int(arg)
            if delay < 1:
                self.reply_message_async("❌ Thời gian phải lớn hơn 0 giây", message_object, thread_id, thread_type, author_id)
                return
            if delay > 300:
                self.reply_message_async("❌ Thời gian tối đa 300 giây (5 phút)", message_object, thread_id, thread_type, author_id)
                return
            config = load_auto_delete_config()
            config["delay"] = delay
            config["enabled"] = True
            save_auto_delete_config(config)
            self.reply_message_async(f"✅ Đã đặt thời gian tự xóa: {delay} giây", message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(f"❌ Lệnh không hợp lệ. Dùng: {self.current_prefix}autodel on/off/<số giây>", message_object, thread_id, thread_type, author_id)

    def handle_command(self, message, author_id, message_object, thread_id, thread_type):
        self._update_prefix()
        message_text = self._get_content_message(message_object)
        if not message_text:
            return

        duyetbox_data = self.client.duyetbox_data
        
        is_admin = check_is_admin(author_id)
        is_duyetbox_thread = (thread_id in duyetbox_data)

        noprefix_handler = self.noprefix_Kryzis.get(message_text.lower())
        if noprefix_handler:
            executor.submit(self._execute_command, noprefix_handler, message_text, message_object, thread_id, thread_type, author_id, message_text.lower())
            return

        special_admin_commands = {
            self.current_prefix + 'cooldown': self._handle_cooldown,
            self.current_prefix + 'credit': self._handle_credit,
            self.current_prefix + 'stw': self._handle_stw,
            self.current_prefix + 'autodel': self._handle_autodel,
        }

        for cmd_prefix_full, handler_func in special_admin_commands.items():
            if message_text.startswith(cmd_prefix_full):
                if re.match(rf"^{re.escape(cmd_prefix_full)}(\s|$)", message_text, re.IGNORECASE):
                    executor.submit(handler_func, message_text, message_object, thread_id, thread_type, author_id)
                    return
        
        found_cmd_name = None
        message_for_execution = message_text
        command_type_reaction = None

        if message_text.startswith(self.current_prefix):
            command_part_after_prefix = message_text[len(self.current_prefix):].strip()
            if command_part_after_prefix:
                potential_command_name_base = command_part_after_prefix.split(' ')[0].lower()
                
                if hasattr(self.client, 'bcmd_handler') and self.client.bcmd_handler.is_command_blocked(potential_command_name_base, author_id, thread_id):
                    self.reply_message_async("Bạn đã bị cấm sử dụng lệnh này.", message_object, thread_id, thread_type, author_id)
                    return

                if potential_command_name_base in self.Kryzis:
                    found_cmd_name = potential_command_name_base
                    command_type_reaction = 'normal'

        if not found_cmd_name and self.stw_commands:
            sorted_valid_stw_cmds = sorted([cmd for cmd in self.stw_commands if cmd in self.Kryzis], key=len, reverse=True)
            if sorted_valid_stw_cmds:
                stw_command_pattern_str = '|'.join([re.escape(cmd) for cmd in sorted_valid_stw_cmds])
                if stw_command_pattern_str:
                    prefix_escaped = re.escape(self.current_prefix)
                    stw_regex = re.compile(rf"{prefix_escaped}\s*({stw_command_pattern_str})(?:\s|$)", re.IGNORECASE)
                    match = stw_regex.search(message_text)
                    if match:
                        found_cmd_name = match.group(1).lower()
                        command_type_reaction = 'stw'

        if found_cmd_name:
            if hasattr(self.client, 'bcmd_handler') and self.client.bcmd_handler.is_command_blocked(found_cmd_name, author_id, thread_id):
                self.reply_message_async("Bạn đã bị cấm sử dụng lệnh này.", message_object, thread_id, thread_type, author_id)
                return

            command_handler = self.Kryzis.get(found_cmd_name)
            if command_handler:
                executor.submit(self._execute_command, command_handler, message_for_execution, message_object, thread_id, thread_type, author_id, found_cmd_name)
            return

        # Xử lý khi chỉ gõ prefix không có lệnh
        if message_text.strip() == self.current_prefix:
            help_message = f"SUCCESS\nDùng {self.current_prefix}menu để xem tất cả lệnh có thể dùng với bot của tui"
            style = MultiMsgStyle([
                MessageStyle(offset=0, length=7, style="bold", auto_format=False),
                MessageStyle(offset=0, length=7, style="color", color="#15A85F", auto_format=False),
                MessageStyle(offset=0, length=10000, style="font", size="1", auto_format=False),
            ])
            self.reply_message_async(help_message, message_object, thread_id, thread_type, author_id, style=style)
            return

        # Phần xử lý lệnh sai
        if message_text.startswith(self.current_prefix):
            command_part_after_prefix = message_text[len(self.current_prefix):].strip()
            wrong_cmd = command_part_after_prefix.split()[0] if command_part_after_prefix else ""
            predicted = self.predict_command(wrong_cmd)
            hint = f"\n💡 Ý bạn là: {self.current_prefix}{predicted}?" if predicted else ""
            help_message = f"ERROR\n    Lệnh '{wrong_cmd}' không tồn tại.{hint}\n    Gõ {self.current_prefix}menu để xem trợ giúp"
            style = MultiMsgStyle([
                MessageStyle(offset=0, length=5, style="bold", auto_format=False),
                MessageStyle(offset=0, length=5, style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=0, length=10000, style="font", size="1", auto_format=False),
            ])
            self.reply_message_async(help_message, message_object, thread_id, thread_type, author_id, style=style)
            return