# app/core/server/live/apiBot.py - FIX PREFIX
from ..client import *
import json
import threading

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
        
        bot_id = bot.get("botIntId")
        is_running = is_bot_running(bot_id)
        
        return jsonify({
            "ok": True, 
            "bot": bot, 
            "file": loginFile,
            "is_running": is_running
        })

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

        def run_bot_thread():
            try:
                from app.core.login.login import RunBot
                RunBot(
                    Imei=imei,
                    SessionCookies=sc,
                    Prefix=prefix,
                    MainBot=False,
                    Username=username,
                    BotIntId=botIntId,
                    Status=True,
                    FilePath=os.path.join("assets", "config", "multibot", str(loginFile))
                )
            except Exception as e:
                print(f"[Web] Lỗi start bot: {e}")

        threading.Thread(target=run_bot_thread, daemon=True).start()

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

        bot_id = bot.get("botIntId")
        offbot(bot)
        
        bot["status"] = False
        bot["isActived"] = False
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
        # Tìm bot theo account
        bot, loginFile, path = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)

        # Cập nhật prefix
        bot["prefix"] = newPrefix
        try:
            _, meta = ReadJSONMeta(path)
            WriteBotANDMeta(path, bot, meta)
        except Exception as e:
            print(f"[Prefix] Lỗi lưu: {e}")
            return Jsonfailed("Không thể lưu prefix", 500)

        # Cập nhật cho bot đang chạy
        target = TargetGet(str(bot.get("botIntId")), bool(bot.get("mainBot", False)))
        try:
            if target is not None:
                setattr(target, "prefix", newPrefix)
        except:
            pass

        return jsonify({"ok": True, "updated": True, "prefix": newPrefix, "file": loginFile})
