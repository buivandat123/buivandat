# app/core/server/live/apiAdmin.py
from ..client import *
from modules.engine.data.data import databaseReader
from modules.services.hook.core_hook.login_hook import LoadAllBotData
from modules.services.index import restartABot, shutdownABot
from src.bot.system import mysys as mysys_info
from datetime import datetime

adminUser = databaseReader().get("adminAcc") or "admin"

def AdminReq():
    if session.get("isAdmin") is not True or str(session.get("account") or "") != adminUser:
        raise Exception("Admin only")
    return adminUser

def BuildSystemInfo():
    totalMb, usedMb = mysys_info.readMemMb()
    return {
        "ramUsedMb": usedMb or "unknown",
        "ramTotalMb": totalMb or "unknown",
        "os": mysys_info.osPretty() or "Linux",
        "cpu": mysys_info.readCpuModel() or "unknown",
        "cpuCores": mysys_info.readCpuCores() or "unknown",
        "uptime": mysys_info.runCmd(["bash", "-lc", "uptime -p 2>/dev/null"]) or "unknown",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

@app.get("/api/admin/overview")
def AdminOverview():
    try:
        AdminReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    bots = LoadAllBotData() or []
    runningCount = sum(1 for b in bots if b.get("status"))
    
    return jsonify({
        "ok": True,
        "clusters": bots,
        "summary": {
            "activeClusters": runningCount,
            "totalClusters": len(bots),
            "stoppedClusters": max(0, len(bots) - runningCount),
        },
        "system": BuildSystemInfo()
    })

@app.post("/api/admin/bot/action")
def AdminBotAction():
    try:
        AdminReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    body = request.get_json(silent=True) or {}
    botIntId = str(body.get("botIntId") or "").strip()
    action = str(body.get("action") or "").strip().lower()

    if not botIntId or not action:
        return Jsonfailed("Missing botIntId or action")

    bots = LoadAllBotData()
    bot = None
    for b in bots:
        if str(b.get("botIntId")) == botIntId:
            bot = b
            break

    if not bot:
        return Jsonfailed("Bot not found", 404)

    if action == "run" or action == "start":
        bot["status"] = True
        bot["isActived"] = True
        restartABot(bot)
        return jsonify({"ok": True, "message": "Bot started"})
    elif action == "stop":
        bot["status"] = False
        bot["isActived"] = False
        shutdownABot(bot)
        return jsonify({"ok": True, "message": "Bot stopped"})
    elif action == "restart":
        bot["status"] = True
        bot["isActived"] = True
        restartABot(bot)
        return jsonify({"ok": True, "message": "Bot restarted"})
    else:
        return Jsonfailed("Invalid action")
