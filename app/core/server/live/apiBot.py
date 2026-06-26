# app/core/server/live/apiBot.py
from ..client import *
import json

@app.get("/api/bot/info")
def BotInfo():
    try:
        account, _ = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    with Lock:
        bot, loginFile, _ = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)
        return jsonify({"ok": True, "bot": bot, "file": loginFile})

@app.post("/api/bot/run")
def BotRun():
    try:
        account, _ = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    with Lock:
        bot, loginFile, path = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)

        sc = bot.get("sessionCookies") or {}
        if not isinstance(sc, dict) or not sc:
            return Jsonfailed("Blank sessionCookies", 400)

        imei = bot.get("imei")
        prefix = bot.get("prefix", "")
        botIntId = bot.get("botIntId")
        username = bot.get("username")

        threading.Thread(
            target=RunBot,
            args=(imei, sc, prefix, False, username, botIntId, True, os.path.join("assets", "config", "multibot", str(loginFile))),
            daemon=True
        ).start()

        bot["status"] = True
        bot["isActived"] = True
        try:
            _, meta = ReadJSONMeta(path)
            WriteBotANDMeta(path, bot, meta)
        except:
            pass

        return jsonify({"ok": True, "started": True, "botAccount": bot.get("botAccount"), "botIntId": botIntId})

@app.post("/api/bot/stop")
def BotStop():
    try:
        account, _ = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    with Lock:
        bot, _, path = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)

        offbot(bot)
        bot["status"] = False
        try:
            _, meta = ReadJSONMeta(path)
            WriteBotANDMeta(path, bot, meta)
        except:
            pass

        return jsonify({"ok": True, "stopped": True})

@app.post("/api/bot/restart")
def BotRestart():
    try:
        account, _ = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    with Lock:
        bot, loginFile, path = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)

        sc = bot.get("sessionCookies") or {}
        if not isinstance(sc, dict) or not sc:
            return Jsonfailed("Blank sessionCookies", 400)

        bot["status"] = True
        bot["isActived"] = True
        try:
            _, meta = ReadJSONMeta(path)
            WriteBotANDMeta(path, bot, meta)
        except:
            pass

        Rsbot(bot, loginFile)
        return jsonify({"ok": True, "restarted": True})
    
@app.post("/api/bot/prefix")
def BotPrefix():
    try:
        account, _ = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    body = request.get_json(silent=True) or {}
    newPrefix = str(body.get("newPrefix") or "").strip()
    if not newPrefix:
        return Jsonfailed("Missing newPrefix")

    with Lock:
        bot, loginFile, path = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)

        bot["prefix"] = newPrefix
        try:
            _, meta = ReadJSONMeta(path)
            WriteBotANDMeta(path, bot, meta)
        except:
            pass

        target = TargetGet(str(bot.get("botIntId")), bool(bot.get("mainBot", False)))
        try:
            if target is not None:
                setattr(target, "prefix", newPrefix)
        except:
            pass

        return jsonify({"ok": True, "updated": True, "prefix": newPrefix, "file": loginFile})
