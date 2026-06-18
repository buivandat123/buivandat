from ..client import *

adminUser = databaseReader().get("adminAcc")
adminPass = databaseReader().get("adminPass")

@app.post("/api/auth/login")
def AuthLogin():
    body = request.get_json(silent=True) or {}
    account = str(body.get("account") or "").strip()
    password = str(body.get("password") or "").strip()
    if not account or not password:
        return Jsonfailed("Missing account/password")

    if SafeEq(account, adminUser) and SafeEq(password, adminPass):
        session["account"] = adminUser
        session["botIntId"] = "admin-dashboard"
        session["loginFile"] = "admin"
        session["isAdmin"] = True
        return jsonify({"ok": True, "account": session["account"], "botIntId": session["botIntId"], "isAdmin": True})

    with Lock:
        bot, loginFile, _ = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)
        if not SafeEq(bot.get("botPassword"), password):
            return Jsonfailed("Wrong password", 401)

        session["account"] = bot.get("botAccount")
        session["botIntId"] = str(bot.get("botIntId") or "")
        session["loginFile"] = str(loginFile)
        session["isAdmin"] = False

        return jsonify({"ok": True, "account": session["account"], "botIntId": session["botIntId"], "isAdmin": False})

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

    bot, _, _ = AccountBot(acc)
    if not bot:
        return jsonify({"ok": False})

    return jsonify({
        "ok": True,
        "account": acc,
        "botIntId": bot.get("botIntId"),
        "username": bot.get("username"),
        "isAdmin": False
    })
