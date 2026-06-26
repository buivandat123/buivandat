# app/core/server/live/apiAuth.py
from ..client import *
from modules.engine.data.data import databaseReader
import json

adminUser = databaseReader().get("adminAcc") or "admin"
adminPass = databaseReader().get("adminPass") or "admin123"

@app.post("/api/auth/login")
def AuthLogin():
    body = request.get_json(silent=True) or {}
    account = str(body.get("account") or "").strip()
    password = str(body.get("password") or "").strip()
    
    print(f"[Auth] Login attempt: account={account}, password={password}")
    
    if not account or not password:
        return Jsonfailed("Missing account/password")

    # Kiểm tra admin
    if SafeEq(account, adminUser) and SafeEq(password, adminPass):
        session["account"] = adminUser
        session["botIntId"] = "admin-dashboard"
        session["loginFile"] = "admin"
        session["isAdmin"] = True
        return jsonify({"ok": True, "account": session["account"], "botIntId": session["botIntId"], "isAdmin": True})

    # Kiểm tra bot con - đọc từ login.json
    try:
        with open("asset/config/login.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"[Auth] Login data: {data}")
        
        for bot in data.get("data", []):
            bot_account = bot.get("botAccount", "")
            bot_password = bot.get("botPassword", "")
            print(f"[Auth] Checking: botAccount={bot_account}, botPassword={bot_password}")
            
            if SafeEq(account, bot_account) and SafeEq(password, bot_password):
                session["account"] = account
                session["botIntId"] = str(bot.get("botIntId") or "")
                session["loginFile"] = bot.get("filePath", "")
                session["isAdmin"] = False
                print(f"[Auth] Login success for bot: {account}")
                return jsonify({
                    "ok": True, 
                    "account": account, 
                    "botIntId": session["botIntId"], 
                    "isAdmin": False,
                    "username": bot.get("username", "")
                })
    except Exception as e:
        print(f"[Auth] Error reading login.json: {e}")
        return Jsonfailed(f"Error: {str(e)}", 500)

    return Jsonfailed("Account not found", 404)

@app.post("/api/auth/logout")
def AuthLogout():
    session.clear()
    return jsonify({"ok": True})

@app.get("/api/auth/me")
def AuthMe():
    acc = session.get("account")
    if not acc:
        return jsonify({"ok": False})

    if session.get("isAdmin") is True and str(acc) == adminUser:
        return jsonify({
            "ok": True,
            "account": adminUser,
            "botIntId": "admin-dashboard",
            "username": "Admin",
            "isAdmin": True
        })

    # Lấy thông tin bot từ session
    botIntId = session.get("botIntId")
    try:
        with open("asset/config/login.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for bot in data.get("data", []):
            if str(bot.get("botIntId")) == str(botIntId):
                return jsonify({
                    "ok": True,
                    "account": acc,
                    "botIntId": botIntId,
                    "username": bot.get("username", ""),
                    "isAdmin": False
                })
    except:
        pass

    return jsonify({"ok": False})
