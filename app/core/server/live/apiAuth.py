# app/core/server/live/apiAuth.py
from ..client import *
from modules.engine.data.data import databaseReader
import json

adminUser = databaseReader().get("adminAcc") or "admin"
adminPass = databaseReader().get("adminPass") or "admin123"

@app.route("/api/auth/login", methods=['GET', 'POST'])
def AuthLogin():
    if request.method == 'GET':
        return jsonify({"ok": False, "error": "Method not allowed, use POST"}), 405
    
    body = request.get_json(silent=True) or {}
    account = str(body.get("account") or "").strip()
    password = str(body.get("password") or "").strip()
    
    print(f"[Auth] Login attempt: account={account}")
    
    if not account or not password:
        return Jsonfailed("Missing account/password")

    # Kiểm tra admin
    if SafeEq(account, adminUser) and SafeEq(password, adminPass):
        session["account"] = adminUser
        session["botIntId"] = "admin-dashboard"
        session["loginFile"] = "admin"
        session["isAdmin"] = True
        session["redirect"] = "/admin/dashboard"
        return jsonify({
            "ok": True, 
            "account": session["account"], 
            "botIntId": session["botIntId"], 
            "isAdmin": True,
            "redirect": "/admin/dashboard"
        })

    # Kiểm tra bot con
    try:
        with open("asset/config/login.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for bot in data.get("data", []):
            bot_account = bot.get("botAccount", "")
            bot_password = bot.get("botPassword", "")
            
            if SafeEq(account, bot_account) and SafeEq(password, bot_password):
                bot_id = str(bot.get("botIntId") or "")
                session["account"] = account
                session["botIntId"] = bot_id
                session["loginFile"] = bot.get("filePath", "")
                session["isAdmin"] = False
                session["redirect"] = f"/bot/{bot_id}/dashboard"
                print(f"[Auth] Login success for bot: {account} -> /bot/{bot_id}/dashboard")
                return jsonify({
                    "ok": True, 
                    "account": account, 
                    "botIntId": bot_id, 
                    "isAdmin": False,
                    "username": bot.get("username", ""),
                    "redirect": f"/bot/{bot_id}/dashboard"
                })
    except Exception as e:
        print(f"[Auth] Error: {e}")
        return Jsonfailed(f"Error: {str(e)}", 500)

    return Jsonfailed("Account not found", 404)

@app.route("/api/auth/logout", methods=['GET', 'POST'])
def AuthLogout():
    session.clear()
    return jsonify({"ok": True})

@app.get("/api/auth/me")
def AuthMe():
    acc = session.get("account")
    if not acc:
        return jsonify({"ok": False})

    if session.get("isAdmin") is True:
        return jsonify({
            "ok": True,
            "account": adminUser,
            "botIntId": "admin-dashboard",
            "username": "Admin",
            "isAdmin": True
        })

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
