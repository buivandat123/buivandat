from functions.services.hook.core_hook.multibot_core import *

def SaveBotField(fp, items, bot, k, v):
    bot[k] = v
    with open(fp, "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=4))

def GetMentionUid(this, data):
    uids = this.extractUids(data) or []
    return str(uids[0]) if uids else None

def HasUserClientId(items, uid):
    uid = str(uid)
    if not isinstance(items, list):
        return False
    for it in items:
        if isinstance(it, dict) and str(it.get("userClientId") or "") == uid:
            return True
    return False

def PickBotItem(items):
    for it in items:
        if isinstance(it, dict) and it.get("botIntId"):
            return it
    return None

def SlugName(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]", "", s).lower()

def ParseTimeExpression(expr):
    s = (expr or "").strip().lower().replace(" ", "")
    if not s:
        return timedelta()
    pattern = r"(\d+)(mo|min|y|w|d|h|m|s)"
    matches = re.findall(pattern, s)
    delta = timedelta()
    for value, unit in matches:
        v = int(value)
        if unit == "y":
            delta += timedelta(days=v * 365)
        elif unit == "mo":
            delta += timedelta(days=v * 30)
        elif unit == "w":
            delta += timedelta(weeks=v)
        elif unit == "d":
            delta += timedelta(days=v)
        elif unit == "h":
            delta += timedelta(hours=v)
        elif unit in ("m", "min"):
            delta += timedelta(minutes=v)
        elif unit == "s":
            delta += timedelta(seconds=v)
    return delta

def ExtractJsonPayload(s):
    s = (s or "").strip()
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
    return m.group(1).strip() if m else None

def SendMention(this, text, userId, threadId, type):
    this.sendMSuccess(text, userId, threadId, type)

def GetUidFrom(data):
    v = getattr(data, "uidFrom", None)
    return str(v) if v is not None else None

def GetOwnBot(this, data, userId, threadId, type):
    uidFrom = getattr(data, "uidFrom", None)
    if not uidFrom:
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None

    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {}) if isinstance(dataConfig.get("dataBot", {}), dict) else {}
    loginFile = dataBot.get(str(uidFrom))
    if not loginFile:
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None

    loginPath = os.path.join("assets", "config", "multibot", loginFile)
    if not os.path.exists(loginPath):
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None

    try:
        items = ReadLoginJson(loginPath)
    except Exception:
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None

    if not HasUserClientId(items, uidFrom):
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None

    bot = PickBotItem(items)
    if not bot:
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None

    return bot, loginPath, items

def BuildBotIndexList():
    dataConfig = jsonLoader(mainLogin) or {}
    mainBots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []

    accountDir = os.path.join("assets", "config", "multibot")
    accountFiles = []
    if os.path.isdir(accountDir):
        for name in os.listdir(accountDir):
            if name.endswith("-login.json"):
                accountFiles.append(os.path.join(accountDir, name))

    seen = set()
    result = []

    def AddBot(bot, src, fp):
        if not isinstance(bot, dict):
            return
        botIntId = str(bot.get("botIntId") or "")
        username = str(bot.get("username") or "")
        imei = str(bot.get("imei") or "")
        key = (botIntId, username, imei)
        if key in seen:
            return
        seen.add(key)
        result.append((bot, src, fp))

    for bot in mainBots:
        AddBot(bot, "MAIN", mainLogin)

    for fp in accountFiles:
        try:
            items = ReadLoginJson(fp)
        except Exception:
            continue
        if not isinstance(items, list):
            continue
        bot = PickBotItem(items)
        if bot:
            AddBot(bot, os.path.basename(fp), fp)

    def SortKey(x):
        bot, src, fp = x
        isMain = 1 if bot.get("mainBot") else 0
        isFromMainDb = 1 if src == "MAIN" else 0
        username = str(bot.get("username") or "").lower()
        botIntId = str(bot.get("botIntId") or "")
        return (-isMain, -isFromMainDb, username, botIntId)

    result.sort(key=SortKey)
    return result

def GetBotByMention(this, data, userId, threadId, type):
    uid = GetMentionUid(this, data)
    if not uid:
        return None, None, None
    if not this.mainBot:
        SendMention(this, "Permission denied", userId, threadId, type)
        return None, None, None

    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {}) if isinstance(dataConfig.get("dataBot", {}), dict) else {}
    loginFile = dataBot.get(uid)
    if not loginFile:
        SendMention(this, "status:unkownUid", userId, threadId, type)
        return None, None, None

    loginPath = os.path.join("assets", "config", "multibot", loginFile)
    if not os.path.exists(loginPath):
        SendMention(this, "status:unkownUid", userId, threadId, type)
        return None, None, None

    items = ReadLoginJson(loginPath)
    if not HasUserClientId(items, uid):
        SendMention(this, "status:unkownUid", userId, threadId, type)
        return None, None, None

    bot = PickBotItem(items)
    if not bot:
        SendMention(this, "status:unkownUid", userId, threadId, type)
        return None, None, None

    return bot, loginPath, items

def GetBotByIndexOrMention(this, data, userId, threadId, type, token=None):
    bot, filePath, items = GetBotByMention(this, data, userId, threadId, type)
    if bot:
        return bot, filePath, items

    if this.mainBot and token and str(token).isdigit():
        idx = int(token)
        arr = BuildBotIndexList()
        if idx < 1 or idx > len(arr):
            SendMention(this, "Index out of range", userId, threadId, type)
            return None, None, None
        bot, src, fp = arr[idx - 1]
        if fp == mainLogin:
            dataConfig = jsonLoader(mainLogin) or {}
            bots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []
            return bot, mainLogin, bots
        items = ReadLoginJson(fp)
        return PickBotItem(items), fp, items

    dataConfig = jsonLoader(mainLogin) or {}
    bots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []
    mybot = next((b for b in bots if str(b.get("botIntId") or "") == str(userId)), None)
    if not mybot:
        SendMention(this, "status:null", userId, threadId, type)
        return None, None, None
    return mybot, mainLogin, bots

def IsMainBotUser(userId):
    dataConfig = jsonLoader(mainLogin) or {}
    bots = dataConfig.get("data", [])
    for b in bots:
        if b.get("mainBot") and str(b.get("botIntId")) == str(userId):
            return True
    return False

def initExpire(this):
    now = datetime.now()
    arr = BuildBotIndexList() or []
    if not arr:
        return

    dataConfig = None
    dataBot = None
    dirtyMainDb = False

    def ParseExpired(s):
        try:
            return datetime.strptime(str(s), "%H:%M:%S-%d/%m/%Y")
        except:
            return None

    def LoadMainDb():
        nonlocal dataConfig, dataBot
        if dataConfig is None:
            dataConfig = jsonLoader(mainLogin) or {}
            dataBot = dataConfig.get("dataBot", {})
            if not isinstance(dataBot, dict):
                dataBot = {}
                dataConfig["dataBot"] = dataBot

    def SaveMainDb():
        nonlocal dataConfig, dirtyMainDb
        if dataConfig is not None and dirtyMainDb:
            saveJson(mainLogin, dataConfig)
            dirtyMainDb = False

    def RemoveDataBotByFile(fp):
        LoadMainDb()
        bn = os.path.basename(fp)
        removed = False
        for k, v in list(dataBot.items()):
            if v == bn:
                del dataBot[k]
                removed = True
        return removed

    for bot, src, fp in arr:
        expStr = (bot or {}).get("expiredTime")
        if not expStr:
            continue

        exp = ParseExpired(expStr)
        if not exp:
            continue

        if now <= exp:
            continue

        wasOn = bool(bot.get("status"))
        bot["status"] = False
        bot["isActived"] = False
        if wasOn:
            try:
                shutdownABot(bot)
            except:
                pass

        expiredDelta = now - exp
        shouldDelete = fp != mainLogin and expiredDelta >= timedelta(days=1)

        if fp == mainLogin:
            LoadMainDb()
            bots = dataConfig.get("data", [])
            if not isinstance(bots, list):
                bots = []
                dataConfig["data"] = bots
            bid = str(bot.get("botIntId") or "")
            for b in bots:
                if isinstance(b, dict) and str(b.get("botIntId") or "") == bid:
                    b["status"] = False
                    b["isActived"] = False
                    dirtyMainDb = True
                    break
            continue

        if shouldDelete:
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except:
                pass
            if RemoveDataBotByFile(fp):
                dirtyMainDb = True
            continue

        try:
            items = ReadLoginJson(fp)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("botIntId"):
                        it["status"] = False
                        it["isActived"] = False
                        break
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(json.dumps(items, ensure_ascii=False, indent=4))
        except:
            pass

    SaveMainDb()

def loopInitExpire(this):
    def _Run():
        while True:
            try:
                initExpire(this)
            except Exception as e:
                logger.errorMeta(f"Expire watcher error: {e}")
            time.sleep(10)

    threading.Thread(target=_Run, daemon=True).start()

def NormalizePath(p):
    s = str(p or "").strip().replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    return s

def GetthisFilePathFromBotManager(this):
    try:
        cfg = loadBotManager() or {}
        arr = cfg.get("data")
        if not isinstance(arr, list):
            return None

        uid = str(getattr(this, "uid", "") or "").strip()
        imei = GetThisImei(this).strip()
        botIntId = GetThisBotIntId(this).strip()

        for it in arr:
            if not isinstance(it, dict):
                continue

            isMain = it.get("mainBot")
            if isMain is None:
                isMain = it.get("this.mainBot")
            if bool(isMain) is True:
                continue

            dbUid = str(it.get("uid") or it.get("this.uid") or "").strip()
            dbImei = str(it.get("imei") or it.get("this.imei") or "").strip()
            dbBotIntId = str(it.get("botIntId") or it.get("this.botIntId") or "").strip()

            ok = (uid and dbUid == uid) or (imei and dbImei == imei) or (botIntId and dbBotIntId == botIntId)
            if not ok:
                continue

            fp = NormalizePath(it.get("filePath"))
            return fp or None

        return None
    except:
        return None
def GetThisImei(this):
    v = getattr(this, "imei", None)
    if v:
        return str(v)
    st = getattr(this, "_state", None)
    v = getattr(st, "imei", None) if st else None
    return str(v) if v else ""

def GetThisBotIntId(this):
    v = getattr(this, "botIntId", None)
    if v:
        return str(v)
    st = getattr(this, "_state", None)
    v = getattr(st, "botIntId", None) if st else None
    return str(v) if v else ""

def MatchthisBotItem(this, it):
    uid = str(getattr(this, "uid", "") or "").strip()
    if uid and str(it.get("uid") or "").strip() == uid:
        return True

    imei = GetThisImei(this)
    if imei and str(it.get("imei") or "").strip() == imei:
        return True

    botIntId = GetThisBotIntId(this)
    if botIntId and str(it.get("botIntId") or "").strip() == botIntId:
        return True

    return False

def GetOwnBotByFilePath(this):
    fp = GetthisFilePathFromBotManager(this)
    if not fp or not os.path.exists(fp):
        return None, None, None

    items = ReadLoginJson(fp)
    if not isinstance(items, list) or not items:
        return None, fp, items

    for it in items:
        if isinstance(it, dict) and MatchthisBotItem(this, it):
            return it, fp, items

    if len(items) == 1 and isinstance(items[0], dict):
        return items[0], fp, items

    return None, fp, items