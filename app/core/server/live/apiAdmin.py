from datetime import datetime, timedelta

from functions.engine.data.data import WriteService
from functions.engine.data.data import ReadServices
from functions.services.hook.core_hook.extra_multibot_core import ParseTimeExpression
from functions.services.hook.core_hook.login_hook import ReadLoginJson, LoadAllBotData
from functions.services.index import restartABot, shutdownABot
from src.bot.system import mysys as mysys_info
from app.core.login import login as core_login
from app.core.server.client import *

adminUser = databaseReader().get("adminAcc")
TIME_FMT = "%H:%M:%S-%d/%m/%Y"


def AdminReq():
    if session.get("isAdmin") is not True or str(session.get("account") or "") != adminUser:
        raise Unauthorized("Admin only")
    return adminUser


def ParseDt(v):
    s = str(v or "").strip()
    if not s:
        return None
    for fmt in ("%H:%M:%S-%d/%m/%Y", "%H:%M:%S/%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except:
            pass
    return None


def FmtDt(dt):
    return dt.strftime(TIME_FMT)


def EnsureMainData(cfg):
    arr = cfg.get("data")
    if isinstance(arr, list):
        return arr
    arr = []
    cfg["data"] = arr
    return arr


def FindBotRecord(botIntId):
    bid = str(botIntId or "").strip()
    if not bid:
        return None, None, None

    dataCfg = jsonLoader(mainLogin) or {}
    for b in EnsureMainData(dataCfg):
        if isinstance(b, dict) and str(b.get("botIntId") or "") == bid:
            return b, mainLogin, dataCfg

    accountDir = os.path.join("assets", "config", "multibot")
    if not os.path.isdir(accountDir):
        return None, None, None

    for fn in os.listdir(accountDir):
        if not fn.endswith("-login.json"):
            continue
        fp = os.path.join(accountDir, fn)
        items = ReadLoginJson(fp)
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, dict) and str(it.get("botIntId") or "") == bid:
                return it, fp, items
    return None, None, None


def SaveBotRecord(filePath, container):
    if filePath == mainLogin:
        saveJson(mainLogin, container)
        return
    saveJson(filePath, container)


def BotRunning(bot):
    bid = str(bot.get("botIntId") or "")
    isMain = bool(bot.get("mainBot", False))
    return TargetGet(bid, isMain) is not None


def BuildSystemInfo():
    totalMb, usedMb = mysys_info.readMemMb()
    osName = mysys_info.osPretty() or "unknown"
    kernel = platform.release() or "unknown"
    pyv = platform.python_version() if hasattr(platform, "python_version") else "unknown"
    cpuModel = mysys_info.readCpuModel() or "unknown"
    cpuCores = mysys_info.readCpuCores() or "unknown"
    loadAvg = mysys_info.readLoadAvg() or "unknown"
    uptime = mysys_info.runCmd(["bash", "-lc", "uptime -p 2>/dev/null"]) or "unknown"
    diskRoot = mysys_info.dfRoot() or "unknown"
    diskPct = mysys_info.parseDfPct()
    vga = "unknown"
    if shutil.which("lspci"):
        vga = mysys_info.firstNonEmpty(
            mysys_info.runCmd(["bash", "-lc", "lspci | grep -E 'VGA compatible controller|3D controller|Display controller' | head -n1 | sed 's/^[^:]*: *//' "]),
            mysys_info.runCmd(["bash", "-lc", "lspci | grep -Ei 'nvidia|amd|intel' | head -n1 | sed 's/^[^:]*: *//' "]),
        ) or "unknown"
    gpuName = "0"
    vram = "unknown"
    vramPct = None
    tempGpu = "unknown"
    if shutil.which("nvidia-smi"):
        gpuName = mysys_info.runCmd(["bash", "-lc", "nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits | head -n1"]) or "0"
        vram = mysys_info.runCmd(["bash", "-lc", "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | head -n1 | sed 's/, */\//'"]) or "unknown"
        t = mysys_info.runCmd(["bash", "-lc", "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -n1"]) or ""
        tempGpu = f"{t}C" if t else "unknown"
        if "/" in vram:
            try:
                used, total = vram.split("/", 1)
                vramPct = int(int(used.strip()) * 100 / max(1, int(total.strip())))
            except:
                vramPct = None
    tempCpu = "unknown"
    if shutil.which("sensors"):
        tempCpu = mysys_info.firstNonEmpty(
            mysys_info.runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/Package id 0:/ {print $4; exit}'"]),
            mysys_info.runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/Tctl:/ {print $2; exit}'"]),
            mysys_info.runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/CPU Temperature:/ {print $3; exit}'"]),
        ) or "unknown"
    ramPct = None
    try:
        if totalMb and usedMb:
            ramPct = int(int(usedMb) * 100 / max(1, int(totalMb)))
    except:
        ramPct = None
    return {
        "os": osName,
        "kernel": kernel,
        "arch": platform.machine() or "unknown",
        "ramUsedMb": usedMb or "unknown",
        "ramTotalMb": totalMb or "unknown",
        "ramPct": ramPct,
        "cpu": cpuModel,
        "cpuCores": cpuCores,
        "cpuLoadAvg": loadAvg,
        "uptime": uptime,
        "diskRoot": diskRoot,
        "diskPct": diskPct if isinstance(diskPct, int) and diskPct >= 0 else None,
        "vga": vga,
        "gpu": gpuName,
        "vram": vram,
        "vramPct": vramPct,
        "tempCpu": tempCpu,
        "tempGpu": tempGpu,
        "software": f"{osName} | kernel {kernel} | python {pyv}",
        "python": pyv,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def BuildCleanBots():
    raw = [PackBot(x) for x in (LoadAllBotData() or []) if isinstance(x, dict)]
    raw = [x for x in raw if isinstance(x, dict) and str(x.get("botIntId") or "").strip()]

    byId = {}
    for b in raw:
        bid = str(b.get("botIntId") or "")
        cur = byId.get(bid)
        if not cur:
            byId[bid] = b
            continue
        scoreCur = (1 if cur.get("mainBot") else 0) + (1 if cur.get("running") else 0)
        scoreNew = (1 if b.get("mainBot") else 0) + (1 if b.get("running") else 0)
        if scoreNew > scoreCur:
            byId[bid] = b

    bots = list(byId.values())
    bots.sort(key=lambda b: (not b.get("mainBot", False), not b.get("running", False), b.get("username") or "", b.get("botIntId") or ""))
    return bots


def PackBot(bot):
    botIntId = str(bot.get("botIntId") or "").strip()
    if not botIntId:
        return None
    expired = ParseDt(bot.get("expiredTime"))
    now = datetime.now()
    return {
        "botIntId": botIntId,
        "username": str(bot.get("username") or ""),
        "botAccount": str(bot.get("botAccount") or ""),
        "prefix": str(bot.get("prefix") or "?"),
        "status": bool(bot.get("status", False)),
        "isActived": bool(bot.get("isActived", False)),
        "mainBot": bool(bot.get("mainBot", False)),
        "login": bot.get("login"),
        "filePath": str(bot.get("filePath") or ""),
        "activedTime": bot.get("activedTime") or "",
        "expiredTime": bot.get("expiredTime") or "",
        "running": BotRunning(bot),
        "isExpired": bool(expired and now > expired),
    }


@app.get("/api/admin/overview")
def AdminOverview():
    try:
        AdminReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    bots = BuildCleanBots()
    clusters = [b for b in bots if not b.get("mainBot")]
    runningCount = sum(1 for x in clusters if x.get("status") and not x.get("isExpired"))
    stoppedCount = max(0, len(clusters) - runningCount)
    sys = BuildSystemInfo()

    return jsonify({
        "ok": True,
        "system": sys,
        "clusters": clusters,
        "summary": {
            "activeClusters": runningCount,
            "totalClusters": len(clusters),
            "stoppedClusters": stoppedCount,
            "ramUsedMb": sys.get("ramUsedMb"),
            "ramTotalMb": sys.get("ramTotalMb"),
            "software": sys.get("software"),
        },
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
    timeExpr = str(body.get("timeExpr") or "").strip()

    if not botIntId:
        return Jsonfailed("Missing botIntId")
    if action not in ("restart", "stop", "run", "add_time", "sub_time"):
        return Jsonfailed("Unsupported action")

    with Lock:
        bot, filePath, container = FindBotRecord(botIntId)
        if not bot:
            return Jsonfailed("Bot not found", 404)
        if bool(bot.get("mainBot", False)):
            return Jsonfailed("Main bot is protected", 400)
        bot["filePath"] = filePath

        now = datetime.now()
        if action in ("add_time", "sub_time"):
            delta = ParseTimeExpression(timeExpr)
            if not delta or delta <= timedelta(0):
                return Jsonfailed("Invalid timeExpr, example: 2d6h or 30m")
            base = ParseDt(bot.get("expiredTime")) or now
            if action == "add_time":
                nxt = (base if base > now else now) + delta
                bot["status"] = True
                bot["isActived"] = True
                if not bot.get("activedTime"):
                    bot["activedTime"] = FmtDt(now)
            else:
                nxt = base - delta
                if nxt <= now:
                    bot["status"] = False
                    bot["isActived"] = False
            bot["expiredTime"] = FmtDt(nxt)
            SaveBotRecord(filePath, container)
            return jsonify({"ok": True, "action": action, "botIntId": botIntId, "expiredTime": bot.get("expiredTime")})

        if action == "stop":
            bot["status"] = False
            bot["isActived"] = False
            SaveBotRecord(filePath, container)
            shutdownABot(bot)
            return jsonify({"ok": True, "action": action, "botIntId": botIntId})

        if action == "run":
            bot["status"] = True
            bot["isActived"] = True
            if not bot.get("activedTime"):
                bot["activedTime"] = FmtDt(now)
            SaveBotRecord(filePath, container)
            restartABot(bot)
            return jsonify({"ok": True, "action": action, "botIntId": botIntId})

        bot["status"] = True
        bot["isActived"] = True
        SaveBotRecord(filePath, container)
        restartABot(bot)
        return jsonify({"ok": True, "action": action, "botIntId": botIntId})


@app.post("/api/admin/bot/delete")
def AdminBotDelete():
    try:
        AdminReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    body = request.get_json(silent=True) or {}
    botIntId = str(body.get("botIntId") or "").strip()
    if not botIntId:
        return Jsonfailed("Missing botIntId")

    with Lock:
        bot, filePath, container = FindBotRecord(botIntId)
        if not bot:
            return Jsonfailed("Bot not found", 404)
        if bool(bot.get("mainBot", False)) or filePath == mainLogin:
            return Jsonfailed("Cannot delete main cluster", 400)

        shutdownABot(bot)

        removedFile = False
        if isinstance(container, list):
            nxt = [it for it in container if str((it or {}).get("botIntId") or "") != botIntId]
            if not nxt:
                try:
                    if os.path.exists(filePath):
                        os.remove(filePath)
                        removedFile = True
                except:
                    pass
            else:
                SaveBotRecord(filePath, nxt)

        if removedFile:
            rootCfg = jsonLoader(mainLogin) or {}
            db = rootCfg.get("dataBot")
            if isinstance(db, dict):
                bn = os.path.basename(filePath)
                for k, v in list(db.items()):
                    if str(v) == bn:
                        del db[k]
                rootCfg["dataBot"] = db
                saveJson(mainLogin, rootCfg)

    return jsonify({"ok": True, "deleted": True, "botIntId": botIntId})


@app.post("/api/admin/system/action")
def AdminSystemAction():
    try:
        AdminReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    body = request.get_json(silent=True) or {}
    action = str(body.get("action") or "").strip().lower()
    text = str(body.get("text") or "").strip()
    if action not in ("restart_all_clusters", "stop_all_clusters", "notify_group"):
        return Jsonfailed("Unsupported action")

    bots = [b for b in BuildCleanBots() if not b.get("mainBot")]

    if action == "notify_group":
        msg = text or "Thong bao he thong tu admin dashboard."
        try:
            gid = core_login.ResolveGroupId()
            mc = getattr(core_login, "mainclient", None)
            if not gid or not mc:
                return Jsonfailed("Notify group is not configured", 400)
            mc.send(Message(text=msg), threadId=gid, type=ThreadType.GROUP)
            return jsonify({"ok": True, "action": action, "sent": True})
        except Exception as e:
            return Jsonfailed(f"Notify fail: {e}", 500)

    done = 0
    with Lock:
        for b in bots:
            try:
                bot, filePath, container = FindBotRecord(b.get("botIntId"))
                if not bot:
                    continue
                if action == "restart_all_clusters":
                    bot["status"] = True
                    bot["isActived"] = True
                    SaveBotRecord(filePath, container)
                    restartABot(bot)
                    done += 1
                elif action == "stop_all_clusters":
                    bot["status"] = False
                    bot["isActived"] = False
                    SaveBotRecord(filePath, container)
                    shutdownABot(bot)
                    done += 1
            except:
                continue

    return jsonify({"ok": True, "action": action, "done": done})


@app.get("/api/admin/system")
def AdminSystem():
    try:
        AdminReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)
    return jsonify({"ok": True, "system": BuildSystemInfo()})


@app.get("/api/bot/admin/list")
def adminList():
    _, botIntId = AuthReq()
    settings = ReadServices(botIntId) or {}
    high = settings.get("highAdmin")
    admin = settings.get("adminBot")
    return jsonify({"ok": True, "high": high, "admin": admin})


@app.get("/api/bot/admin/list/adminBot")
def adminBotList():
    _, botIntId = AuthReq()
    settings = ReadServices(botIntId) or {}
    admin = settings.get("adminBot")
    return jsonify({"ok": True, "admin": admin})


@app.get("/api/bot/admin/list/highAdmin")
def highAdminList():
    _, botIntId = AuthReq()
    settings = ReadServices(botIntId) or {}
    high = settings.get("highAdmin")
    return jsonify({"ok": True, "high": high})


@app.route("/api/bot/admin/add", methods=["POST"])
def adminAdd():
    _, botIntId = AuthReq()
    settings = ReadServices(botIntId) or {}
    data = request.get_json() or {}
    uid = data.get("id")
    if not uid:
        return jsonify({"ok": False, "error": "Missing id"})
    if uid in settings.get("highAdmin", []):
        return jsonify({"ok": False, "error": "Already high admin"})
    if uid in settings.get("adminBot", []):
        return jsonify({"ok": False, "error": "Already admin"})
    settings.setdefault("highAdmin", []).append(uid)
    WriteService(botIntId, settings)
    return jsonify({"ok": True})


@app.route("/api/bot/admin/remove", methods=["POST"])
def adminRemove():
    _, botIntId = AuthReq()
    settings = ReadServices(botIntId) or {}
    data = request.get_json() or {}
    uid = data.get("id")
    if not uid:
        return jsonify({"ok": False, "error": "Missing id"})
    if uid not in settings.get("highAdmin", []):
        return jsonify({"ok": False, "error": "Not high admin"})
    settings.setdefault("highAdmin", []).remove(uid)
    WriteService(botIntId, settings)
    return jsonify({"ok": True})


@app.get("/api/bot/getadminavatar")
def getAdminAvatar():
    idGet = request.args.get("id")
    if not idGet:
        return jsonify({"ok": False, "error": "Missing id"})
    try:
        t = TargetGet(str(idGet), False)
        if not t:
            return jsonify({"ok": False, "error": "Bot not running"})
        ap = t.getAvatar(idGet).get('bk_full_avatar')
        return jsonify({"ok": True, "avatarUrl": ap})
    except Exception as e:
        return Jsonfailed(str(e), 500)


@app.get("/api/bot/getalladminavatar")
def getAllAdminAvatar():
    _, botIntId = AuthReq()
    settings = ReadServices(botIntId) or {}
    highAdmin = settings.get("highAdmin", [])
    adminBot = settings.get("adminBot", [])
    allAdmin = highAdmin + adminBot
    avatarList = []
    for admin in allAdmin:
        try:
            t = TargetGet(str(admin), False)
            if not t:
                continue
            ap = t.getAvatar(admin).get('bk_full_avatar')
            avatarList.append({"id": admin, "avatarUrl": ap})
        except:
            continue
    return jsonify({"ok": True, "avatarList": avatarList})
