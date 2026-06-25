# modules/taixiu.py
# -*- coding: utf-8 -*-
import random
import time
import json
import os
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "Kryzis",
    "description": "Game Tài Xỉu",
    "power": "User"
}

# ============================================================
# CONFIG
# ============================================================

DATA_FILE = "data/taixiu_data.json"
os.makedirs("data", exist_ok=True)

# ============================================================
# STYLE
# ============================================================

def _sty(text, color="#e8eaf6", font_size="9"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=font_size, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def sty_ok(t):   return _sty(t, "#15A85F")
def sty_warn(t): return _sty(t, "#F7B503")
def sty_err(t):  return _sty(t, "#DB342E")
def sty_info(t): return _sty(t, "#00BFFF")
def sty_gold(t): return _sty(t, "#FFD700")

def _reply(client, obj, tid, ttype, text, sty=sty_info, ttl=60000):
    msg = Message(text=text, style=sty(text))
    return client.replyMessage(msg, obj, thread_id=tid, thread_type=ttype, ttl=ttl)

# ============================================================
# DATA
# ============================================================

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_data(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "balance": 1000,
            "total_bet": 0,
            "total_win": 0,
            "total_lose": 0,
            "streak": 0,
            "max_streak": 0,
            "last_daily": 0,
            "games": []
        }
        save_data(data)
    return data[uid]

def save_user_data(uid, user_data):
    data = load_data()
    data[str(uid)] = user_data
    save_data(data)

# ============================================================
# GAME
# ============================================================

def roll_dice():
    return [random.randint(1, 6) for _ in range(3)]

def calculate_result(dice):
    total = sum(dice)
    if total >= 11:
        return "TÀI", total
    else:
        return "XỈU", total

def get_user_name_by_id(client, author_id):
    try:
        user_info = client.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except:
        return "Người dùng"

# ============================================================
# HANDLER
# ============================================================

def handle_taixiu(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        _reply(client, message_object, thread_id, thread_type,
               f"""🎲 TÀI XỈU - HƯỚNG DẪN

📋 LỆNH:
.tx tài 100     - Đặt Tài 100 xu
.tx xỉu all     - Đặt Xỉu tất cả
.tx tài 70%     - Đặt Tài 70% số dư
.tx info        - Thông tin của bạn
.tx top         - Bảng xếp hạng
.tx daily       - Nhận thưởng ngày

💡 Mỗi ngày nhận 100 xu miễn phí!""", sty_info, ttl=60000)
        return
    
    action = parts[1].lower()
    user_data = get_user_data(author_id)
    
    # ===== INFO =====
    if action == "info":
        _reply(client, message_object, thread_id, thread_type,
               f"""📊 THÔNG TIN CỦA BẠN

💰 Số dư: {user_data['balance']} xu
🎯 Tổng cược: {user_data['total_bet']} xu
🏆 Thắng: {user_data['total_win']} xu
💔 Thua: {user_data['total_lose']} xu
🔥 Streak: {user_data['streak']}
🏅 Max streak: {user_data['max_streak']}
📅 Lượt chơi: {len(user_data['games'])}""", sty_info, ttl=60000)
        return
    
    # ===== DAILY =====
    if action == "daily":
        last_daily = user_data.get('last_daily', 0)
        now = time.time()
        if now - last_daily < 86400:
            remaining = 86400 - (now - last_daily)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            _reply(client, message_object, thread_id, thread_type,
                   f"⏳ Còn {hours}h {minutes}m nữa mới nhận được!", sty_warn)
            return
        
        user_data['balance'] += 100
        user_data['last_daily'] = now
        save_user_data(author_id, user_data)
        
        _reply(client, message_object, thread_id, thread_type,
               f"🎁 Nhận thưởng ngày +100 xu!\n💰 Số dư: {user_data['balance']} xu", sty_ok)
        return
    
    # ===== TOP =====
    if action == "top":
        data = load_data()
        top_users = sorted(data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:10]
        
        if not top_users:
            _reply(client, message_object, thread_id, thread_type, "📋 Chưa có dữ liệu!", sty_info)
            return
        
        msg = "🏆 BẢNG XẾP HẠNG\n\n"
        for i, (uid, d) in enumerate(top_users, 1):
            try:
                name = client.fetchUserInfo(uid).changed_profiles.get(str(uid), {}).get("displayName", uid)
            except:
                name = uid[:8]
            msg += f"{i}. {name} - {d.get('balance', 0)} xu\n"
        
        _reply(client, message_object, thread_id, thread_type, msg, sty_gold, ttl=60000)
        return
    
    # ===== ĐẶT CƯỢC =====
    if action not in ["tài", "xiu", "tai", "xiu"]:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Sai lệnh! Dùng: .tx tài 100 hoặc .tx xỉu 50", sty_err)
        return
    
    # Chuẩn hóa
    if action in ["tai", "tài"]:
        choice = "TÀI"
    else:
        choice = "XỈU"
    
    if len(parts) < 3:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Nhập số tiền cược!\n💡 .tx {action} 100", sty_err)
        return
    
    # ===== XỬ LÝ TIỀN CƯỢC =====
    bet_str = parts[2].lower()
    
    if bet_str == "all":
        bet = user_data['balance']
    elif bet_str.endswith("%"):
        try:
            percent = int(bet_str[:-1])
            if percent < 1 or percent > 100:
                _reply(client, message_object, thread_id, thread_type, "❌ % từ 1-100!", sty_err)
                return
            bet = int(user_data['balance'] * percent / 100)
        except:
            _reply(client, message_object, thread_id, thread_type, "❌ % không hợp lệ!", sty_err)
            return
    else:
        try:
            bet = int(bet_str)
        except:
            _reply(client, message_object, thread_id, thread_type, "❌ Số tiền không hợp lệ!", sty_err)
            return
    
    if bet <= 0:
        _reply(client, message_object, thread_id, thread_type, "❌ Số tiền phải lớn hơn 0!", sty_err)
        return
    
    if bet > user_data['balance']:
        _reply(client, message_object, thread_id, thread_type,
               f"❌ Bạn không đủ tiền! Số dư: {user_data['balance']} xu", sty_warn)
        return
    
    # ===== LẮC XÚC XẮC =====
    dice = roll_dice()
    result, total = calculate_result(dice)
    win = (result == choice)
    
    # ===== XỬ LÝ =====
    user_data['total_bet'] += bet
    
    if win:
        user_data['balance'] += bet
        user_data['total_win'] += bet
        user_data['streak'] = user_data['streak'] + 1 if user_data['streak'] > 0 else 1
        if user_data['streak'] > user_data['max_streak']:
            user_data['max_streak'] = user_data['streak']
    else:
        user_data['balance'] -= bet
        user_data['total_lose'] += bet
        user_data['streak'] = user_data['streak'] - 1 if user_data['streak'] < 0 else -1
    
    # Lưu lịch sử
    game_record = {
        "time": datetime.now().strftime("%H:%M %d/%m"),
        "bet": bet,
        "choice": choice,
        "result": result,
        "total": total,
        "dice": dice,
        "win": win
    }
    user_data['games'].append(game_record)
    if len(user_data['games']) > 50:
        user_data['games'] = user_data['games'][-50:]
    
    save_user_data(author_id, user_data)
    
    # ===== GỬI KẾT QUẢ =====
    emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    dice_text = " ".join([emojis.get(d, "🎲") for d in dice])
    
    msg = f"""🎲 KẾT QUẢ TÀI XỈU

{dice_text} = {total} điểm

📊 Bạn chọn: {choice}
🎯 Kết quả: {result}
{'🎉 THẮNG' if win else '💔 THUA'} {bet} xu!
💰 Số dư: {user_data['balance']} xu
🔥 Streak: {user_data['streak']}
📊 Tổng cược: {user_data['total_bet']} xu"""
    
    _reply(client, message_object, thread_id, thread_type, msg, sty_ok if win else sty_err, ttl=60000)

# ============================================================
# LOAD
# ============================================================

def Kryzis():
    return {'tx': handle_taixiu}