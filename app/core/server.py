# app/core/server.py
# -*- coding: utf-8 -*-
import os
import json
import time
import subprocess
import sys
import signal
from flask import render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from modules.login_hook import *

# ============================================================
# IMPORT MAINBOT ĐÚNG CÁCH
# ============================================================

def get_main_bot_class():
    """Import MainBot từ main.py"""
    try:
        sys.path.insert(0, os.getcwd())
        from main import MainBot
        return MainBot
    except Exception as e:
        print(f"Lỗi import MainBot: {e}")
        return None

# ============================================================
# BOT PROCESS MANAGEMENT
# ============================================================

def start_bot_process(bot):
    """Chạy bot con trong thread riêng"""
    try:
        bot_id = bot.get("botIntId")
        imei = bot.get("imei")
        session_cookies = bot.get("sessionCookies")
        bot_prefix = bot.get("prefix", "!")
        
        # Lấy api_key và secret_key từ config
        try:
            from asset.config import API_KEY, SECRET_KEY
        except:
            API_KEY = ""
            SECRET_KEY = ""
        
        if not imei or not session_cookies:
            return False, "Thiếu IMEI hoặc Cookies!"
        
        # Dừng bot cũ nếu có
        stop_bot_process(bot_id)
        time.sleep(0.5)
        
        # Chạy bot trong thread (cách đơn giản nhất)
        def run_bot():
            try:
                MainBot = get_main_bot_class()
                if not MainBot:
                    print("Không thể import MainBot")
                    return
                
                bot = MainBot(
                    api_key=API_KEY,
                    secret_key=SECRET_KEY,
                    imei=imei,
                    session_cookies=session_cookies
                )
                bot.settings = {"prefix": bot_prefix}
                bot._bot_enabled = True
                bot.listen()
            except Exception as e:
                print(f"Bot lỗi: {e}")
                import traceback
                traceback.print_exc()
        
        import threading
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        
        # Lưu thread ID
        pid_file = f"data/bot_{bot_id}.pid"
        with open(pid_file, "w") as f:
            f.write(str(thread.ident))
        
        return True, f"Bot đã chạy (Thread ID: {thread.ident})"
    except Exception as e:
        return False, str(e)

def stop_bot_process(bot_id):
    """Dừng bot (chỉ xóa file, không kill thread vì là daemon)"""
    try:
        pid_file = f"data/bot_{bot_id}.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
            return True
        return False
    except:
        return False

def is_bot_running(bot_id):
    """Kiểm tra bot có đang chạy không"""
    try:
        pid_file = f"data/bot_{bot_id}.pid"
        return os.path.exists(pid_file)
    except:
        return False

# ============================================================
# AUTH
# ============================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def bot_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bot_id = kwargs.get('bot_id')
        if not bot_id or session.get('bot_logged_in') != bot_id:
            return redirect(url_for('bot_login', bot_id=bot_id))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# HÀM HỖ TRỢ
# ============================================================

def get_all_bots():
    all_bots = []
    
    try:
        data = jsonLoader("asset/config/login.json")
        if data.get("data"):
            for item in data["data"]:
                if isinstance(item, dict):
                    item["type"] = "main"
                    all_bots.append(item)
    except:
        pass
    
    multibot_dir = "asset/config/multibot"
    if os.path.exists(multibot_dir):
        for filename in os.listdir(multibot_dir):
            if filename.endswith("-login.json"):
                filepath = os.path.join(multibot_dir, filename)
                items = ReadLoginJson(filepath)
                for item in items:
                    if isinstance(item, dict):
                        item["type"] = "sub"
                        item["filePath"] = filepath
                        bot_id = item.get("botIntId")
                        if bot_id:
                            item["is_running"] = is_bot_running(bot_id)
                        all_bots.append(item)
    
    return all_bots

def get_bot_by_id(bot_id):
    bots = get_all_bots()
    for bot in bots:
        if str(bot.get("botIntId")) == str(bot_id):
            return bot
        if str(bot.get("imei")) == str(bot_id):
            return bot
    return None

def verify_bot_password(bot_id, password):
    bot = get_bot_by_id(bot_id)
    if bot:
        return bot.get("botPassword") == password
    return False

def save_bot(bot):
    """Lưu bot vào file đúng"""
    try:
        bot_id = bot.get("botIntId")
        if not bot_id:
            return False
        
        data = jsonLoader(mainLogin) or {}
        dataBot = data.get("dataBot", {})
        login_file = dataBot.get(str(bot_id))
        
        if login_file:
            login_path = os.path.join(os.path.dirname(mainLogin), "multibot", login_file)
            if os.path.exists(login_path):
                items = ReadLoginJson(login_path)
                for i, item in enumerate(items):
                    if str(item.get("botIntId")) == str(bot_id):
                        items[i] = bot
                        break
                with open(login_path, "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=4, ensure_ascii=False)
                return True
        
        data = jsonLoader(mainLogin) or {}
        bots = data.get("data", [])
        for i, b in enumerate(bots):
            if str(b.get("botIntId")) == str(bot_id):
                bots[i] = bot
                break
        data["data"] = bots
        saveJson(mainLogin, data)
        return True
    except:
        return False

def delete_bot(bot_id):
    """Xóa bot"""
    try:
        stop_bot_process(bot_id)
        
        data = jsonLoader(mainLogin) or {}
        dataBot = data.get("dataBot", {})
        login_file = dataBot.get(str(bot_id))
        if login_file:
            login_path = os.path.join(os.path.dirname(mainLogin), "multibot", login_file)
            if os.path.exists(login_path):
                os.remove(login_path)
            del dataBot[str(bot_id)]
            data["dataBot"] = dataBot
            saveJson(mainLogin, data)
        
        bots = data.get("data", [])
        data["data"] = [b for b in bots if str(b.get("botIntId")) != str(bot_id)]
        saveJson(mainLogin, data)
        
        pid_file = f"data/bot_{bot_id}.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
        
        return True
    except:
        return False

# ============================================================
# ROUTES
# ============================================================

def init_routes(app):
    
    # ===== ADMIN LOGIN =====
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            password = request.form.get('password')
            # Lấy mật khẩu từ biến môi trường hoặc file config
            admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
            try:
                config = jsonLoader("asset/config/server_config.json") or {}
                admin_pass = config.get('admin_password', admin_pass)
            except:
                pass
            if password == admin_pass:
                session['admin_logged_in'] = True
                return redirect(url_for('admin_dashboard'))
            return render_template('admin/login.html', error='Sai mật khẩu!')
        return render_template('admin/login.html')
    
    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_logged_in', None)
        return redirect(url_for('admin_login'))
    
    # ===== ADMIN DASHBOARD =====
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        return render_template('admin/dashboard.html')
    
    @app.route('/admin/api/bots')
    @admin_required
    def admin_api_bots():
        bots = get_all_bots()
        return jsonify({"ok": True, "bots": bots})
    
    @app.route('/admin/api/bot/action', methods=['POST'])
    @admin_required
    def admin_api_bot_action():
        data = request.json
        bot_id = data.get('bot_id')
        action = data.get('action')
        
        if not bot_id or not action:
            return jsonify({"ok": False, "error": "Missing bot_id or action"}), 400
        
        bot = get_bot_by_id(bot_id)
        if not bot:
            return jsonify({"ok": False, "error": "Bot not found"}), 404
        
        if action == "approve":
            bot["status"] = True
            bot["isActived"] = True
            bot["approved"] = True
            save_bot(bot)
            success, msg = start_bot_process(bot)
            return jsonify({"ok": success, "message": msg})
            
        elif action == "start":
            bot["status"] = True
            bot["isActived"] = True
            save_bot(bot)
            success, msg = start_bot_process(bot)
            return jsonify({"ok": success, "message": msg})
            
        elif action == "stop":
            bot["status"] = False
            bot["isActived"] = False
            save_bot(bot)
            success = stop_bot_process(bot_id)
            return jsonify({"ok": success, "message": "Bot đã dừng" if success else "Lỗi dừng bot"})
            
        elif action == "restart":
            stop_bot_process(bot_id)
            time.sleep(1)
            bot["status"] = True
            bot["isActived"] = True
            save_bot(bot)
            success, msg = start_bot_process(bot)
            return jsonify({"ok": success, "message": msg})
            
        elif action == "delete":
            success = delete_bot(bot_id)
            return jsonify({"ok": success, "deleted": True})
        else:
            return jsonify({"ok": False, "error": "Invalid action"}), 400
    
    # ===== BOT LOGIN =====
    @app.route('/bot/<bot_id>/login', methods=['GET', 'POST'])
    def bot_login(bot_id):
        bot = get_bot_by_id(bot_id)
        if not bot:
            return "Bot không tồn tại!", 404
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == bot.get("botAccount") and password == bot.get("botPassword"):
                session['bot_logged_in'] = bot_id
                return redirect(url_for('bot_dashboard', bot_id=bot_id))
            return render_template('bot/login.html', bot=bot, error='Sai tên đăng nhập hoặc mật khẩu!')
        
        return render_template('bot/login.html', bot=bot)
    
    @app.route('/bot/<bot_id>/logout')
    def bot_logout(bot_id):
        session.pop('bot_logged_in', None)
        return redirect(url_for('bot_login', bot_id=bot_id))
    
    # ===== BOT DASHBOARD =====
    @app.route('/bot/<bot_id>')
    @bot_login_required
    def bot_dashboard(bot_id):
        bot = get_bot_by_id(bot_id)
        if not bot:
            return "Bot không tồn tại!", 404
        bot["is_running"] = is_bot_running(bot_id)
        return render_template('bot/dashboard.html', bot=bot)
    
    @app.route('/bot/<bot_id>/api/info')
    @bot_login_required
    def bot_api_info(bot_id):
        bot = get_bot_by_id(bot_id)
        if not bot:
            return jsonify({"ok": False, "error": "Bot not found"}), 404
        bot["is_running"] = is_bot_running(bot_id)
        return jsonify({"ok": True, "bot": bot})
    
    @app.route('/bot/<bot_id>/api/update', methods=['POST'])
    @bot_login_required
    def bot_api_update(bot_id):
        data = request.json
        bot = get_bot_by_id(bot_id)
        if not bot:
            return jsonify({"ok": False, "error": "Bot not found"}), 404
        
        if data.get('prefix'):
            old_prefix = bot.get("prefix")
            bot["prefix"] = data.get('prefix')
            save_bot(bot)
            
            if is_bot_running(bot_id):
                stop_bot_process(bot_id)
                time.sleep(1)
                start_bot_process(bot)
            
            return jsonify({"ok": True, "message": f"Đã đổi prefix từ {old_prefix} thành {bot.get('prefix')}"})
        
        return jsonify({"ok": False, "error": "No update data"}), 400
    
    # ===== ROOT =====
    @app.route('/')
    def index():
        return redirect(url_for('admin_login'))
