from app.core.server.libs import *

def Jsonfailed(msg, code=400):
    return jsonify({"ok": False, "error": str(msg)}), code

def SafeEq(a, b):
    a = str(a or "")
    b = str(b or "")
    if len(a) != len(b):
        return False
    r = 0
    for x, y in zip(a.encode(), b.encode()):
        r |= x ^ y
    return r == 0

def AuthReq():
    account = session.get("account")
    botIntId = session.get("botIntId")
    if not account or not botIntId:
        raise Unauthorized("Unauthorized")
    return str(account), str(botIntId)

def DatabaseConfig(cfg):
    try:
        from pymongo import MongoClient
        host = cfg.get("host", "localhost")
        port = int(cfg.get("port", 27017))
        user = cfg.get("user", "")
        password = cfg.get("password", "")
        auth_source = cfg.get("authSource", "admin")
        
        if user and password:
            uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource={auth_source}"
        else:
            uri = f"mongodb://{host}:{port}/"
        
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        return client
    except:
        return None

def TargetGet(botIntId, isMain):
    if isMain:
        e = getClient.getMain()
        return e.client if e else None
    e = getClient.get(str(botIntId))
    return e.client if e else None

def DelTarget(target):
    if not target:
        return False
    try:
        if hasattr(target, "stopListening"):
            target.stopListening()
        else:
            b = getattr(target, "bools", None)
            if b:
                b.shutdown(wait=False)
            if hasattr(target, "listening"):
                target.listening = False
        return True
    except:
        return False

def ReadJSON(loginFile):
    p = os.path.join("assets", "config", "multibot", str(loginFile))
    if not os.path.exists(p):
        return None, None
    try:
        with open(p, "r", encoding="utf-8") as f:
            items = json.load(f)
        bot = items[0] if isinstance(items, list) and items and isinstance(items[0], dict) else None
        return bot, p
    except:
        return None, p

def ReadJSONMeta(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)
        bot = items[0] if isinstance(items, list) and items and isinstance(items[0], dict) else None
        meta = items[1] if isinstance(items, list) and len(items) > 1 and isinstance(items[1], dict) else {}
        return bot, meta
    except:
        return None, {}

def WriteBotANDMeta(path, bot, meta):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([bot, meta or {}], f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def AccountBot(account):
    cfg = jsonLoader(mainLogin) or {}
    dataBot = cfg.get("dataBot") or {}
    if not isinstance(dataBot, dict):
        return None, None, None
    for _, loginFile in dataBot.items():
        bot, path = ReadJSON(loginFile)
        if bot and str(bot.get("botAccount") or "") == str(account):
            return bot, loginFile, path
    return None, None, None

def Rsbot(bot, loginFile):
    username = bot.get("username")
    botIntId = str(bot.get("botIntId"))
    imei = bot.get("imei")
    cookies = bot.get("sessionCookies")
    prefix = bot.get("prefix", "?")
    isMain = bool(bot.get("mainBot", False))
    status = bot.get("status", True)

    target = TargetGet(botIntId, isMain)
    DelTarget(target)
    time.sleep(0.8)

    threading.Thread(
        target=RunBot,
        args=(imei, cookies, prefix, isMain, username, botIntId, status, os.path.join("assets", "config", "multibot", str(loginFile))),
        daemon=True
    ).start()

def offbot(bot):
    botIntId = str(bot.get("botIntId"))
    isMain = bool(bot.get("mainBot", False))
    target = TargetGet(botIntId, isMain)
    DelTarget(target)
    time.sleep(0.8)