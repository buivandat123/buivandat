# modules/mybot.py
# -*- coding: utf-8 -*-
import os
import json
import time
import random
import re
import threading
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType, Mention
import pytz

des = {
    'version': "2.0.0",
    'credits': "T Q D",
    'description': "Quản lý hệ thống bot đa người dùng",
    'power': "Quản trị viên và thành viên"
}

PREFIX = "."
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mainLogin = os.path.join(BASE_DIR, "asset", "config", "main_login.json")
BOT_MANAGER_FILE = os.path.join(BASE_DIR, "asset", "config", "bot-manager-database.json")

# ============================================================
# INIT MAIN LOGIN
# ============================================================

def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        pass

def jsonLoader(filename):
    if not os.path.exists(filename):
        try:
            ensure_dir(os.path.dirname(filename))
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        except:
            pass
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def saveJson(filename, data):
    try:
        ensure_dir(os.path.dirname(filename))
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def init_main_login():
    """Tạo file main_login.json nếu chưa có hoặc bị rỗng"""
    if not os.path.exists(mainLogin):
        ensure_dir(os.path.dirname(mainLogin))
        default_data = {
            "data": [],
            "dataBot": {}
        }
        saveJson(mainLogin, default_data)
        return True
    
    try:
        data = jsonLoader(mainLogin)
        if not isinstance(data, dict):
            data = {}
        if "data" not in data:
            data["data"] = []
        if "dataBot" not in data:
            data["dataBot"] = {}
        saveJson(mainLogin, data)
        return True
    except:
        return False

# Khởi tạo main_login.json
init_main_login()

# ============================================================
# CONFIG HELPER
# ============================================================

def ReadLoginJson(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.loads(f.read() or "[]")
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            return data["data"]
        return []
    except:
        return []

def loadBotManager():
    return jsonLoader(BOT_MANAGER_FILE) or {}

def botManagerSave(cfg):
    saveJson(BOT_MANAGER_FILE, cfg)

def dataGroup(cfg):
    dg = cfg.get("dataGroup")
    if isinstance(dg, dict):
        return dg
    dg = {}
    cfg["dataGroup"] = dg
    return dg

def ensureBotManagerData(cfg):
    arr = cfg.get("data")
    if isinstance(arr, list):
        return arr
    arr = []
    cfg["data"] = arr
    return arr

def NormalizePath(p):
    s = str(p or "").strip().replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    return s

# ============================================================
# STYLE
# ============================================================

def _sty(text, color="#e8eaf6", font_size="9"):
    h = len(text.split("\n")[0]) + 1
    from zlapi.models import MultiMsgStyle, MessageStyle
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=font_size, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def sty_ok(t):   return _sty(t, "#15A85F")
def sty_warn(t): return _sty(t, "#F7B503")
def sty_err(t):  return _sty(t, "#DB342E")
def sty_info(t): return _sty(t, "#00BFFF")

def _reply(client, obj, tid, ttype, text, sty=sty_info, ttl=60000):
    msg = Message(text=text, style=sty(text))
    return client.replyMessage(msg, obj, thread_id=tid, thread_type=ttype, ttl=ttl)

def SendMention(client, text, uid, thread_id, thread_type):
    try:
        name = client.fetchUserInfo(uid).changed_profiles.get(str(uid), {}).get("displayName", str(uid))
    except:
        name = str(uid)
    tag = f"@{name}"
    info = json.dumps([{"pos": 0, "uid": str(uid), "len": len(tag)}])
    msg = Message(text=f"{tag}\n{text}", mention=info)
    client.sendMentionMessage(msg, thread_id)

# ============================================================
# CORE FUNCTIONS
# ============================================================

def IsMainBotUser(userId):
    dataConfig = jsonLoader(mainLogin) or {}
    bots = dataConfig.get("data", [])
    for b in bots:
        if b.get("mainBot") and str(b.get("botIntId")) == str(userId):
            return True
    return False

def GetMentionUid(data):
    ms = getattr(data, "mentions", None) or []
    for m in ms:
        try:
            uid = m.get("uid") if isinstance(m, dict) else getattr(m, "uid", None)
            if uid:
                return str(uid)
        except:
            pass
    return None

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
    import unicodedata
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

def GetUidFrom(data):
    v = getattr(data, "uidFrom", None)
    return str(v) if v is not None else None

def BuildBotIndexList():
    dataConfig = jsonLoader(mainLogin) or {}
    mainBots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []

    accountDir = os.path.join(os.path.dirname(mainLogin), "multibot")
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
        except:
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

def GetOwnBotByFilePath(this):
    cfg = loadBotManager() or {}
    arr = cfg.get("data")
    if not isinstance(arr, list):
        return None, None, None

    uid = str(getattr(this, "uid", "") or "").strip()
    imei = getattr(this, "imei", "") if hasattr(this, "imei") else ""
    botIntId = str(getattr(this, "botIntId", "") or "").strip()

    fp = None
    for it in arr:
        if not isinstance(it, dict):
            continue
        dbUid = str(it.get("this.uid") or "").strip()
        dbImei = str(it.get("this.imei") or "").strip()
        dbBotIntId = str(it.get("this.botIntId") or "").strip()
        if (uid and dbUid == uid) or (imei and dbImei == imei) or (botIntId and dbBotIntId == botIntId):
            fp = NormalizePath(it.get("filePath"))
            break

    if not fp or not os.path.exists(fp):
        return None, fp, None

    items = ReadLoginJson(fp)
    if not isinstance(items, list) or not items:
        return None, fp, items

    for it in items:
        if isinstance(it, dict) and str(it.get("botIntId") or "") == botIntId:
            return it, fp, items

    if len(items) == 1 and isinstance(items[0], dict):
        return items[0], fp, items

    return None, fp, items

def GetOwnBot(this, data, userId, threadId, thread_type):
    uidFrom = GetUidFrom(data)
    if not uidFrom:
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None

    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {}) if isinstance(dataConfig.get("dataBot", {}), dict) else {}
    loginFile = dataBot.get(str(uidFrom))
    if not loginFile:
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None

    loginPath = os.path.join(os.path.dirname(mainLogin), "multibot", loginFile)
    if not os.path.exists(loginPath):
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None

    try:
        items = ReadLoginJson(loginPath)
    except:
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None

    if not HasUserClientId(items, uidFrom):
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None

    bot = PickBotItem(items)
    if not bot:
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None

    return bot, loginPath, items

def GetBotByMention(this, data, userId, threadId, thread_type):
    uid = GetMentionUid(data)
    if not uid:
        return None, None, None
    # Cho phép tất cả user có bot
    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {}) if isinstance(dataConfig.get("dataBot", {}), dict) else {}
    loginFile = dataBot.get(uid)
    if not loginFile:
        SendMention(this, "status:unkownUid", userId, threadId, thread_type)
        return None, None, None

    loginPath = os.path.join(os.path.dirname(mainLogin), "multibot", loginFile)
    if not os.path.exists(loginPath):
        SendMention(this, "status:unkownUid", userId, threadId, thread_type)
        return None, None, None

    items = ReadLoginJson(loginPath)
    if not HasUserClientId(items, uid):
        SendMention(this, "status:unkownUid", userId, threadId, thread_type)
        return None, None, None

    bot = PickBotItem(items)
    if not bot:
        SendMention(this, "status:unkownUid", userId, threadId, thread_type)
        return None, None, None

    return bot, loginPath, items

def GetBotByIndexOrMention(this, data, userId, threadId, thread_type, token=None):
    bot, filePath, items = GetBotByMention(this, data, userId, threadId, thread_type)
    if bot:
        return bot, filePath, items

    if token and str(token).isdigit():
        idx = int(token)
        arr = BuildBotIndexList()
        if idx < 1 or idx > len(arr):
            SendMention(this, "Index out of range", userId, threadId, thread_type)
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
        SendMention(this, "status:null", userId, threadId, thread_type)
        return None, None, None
    return mybot, mainLogin, bots

def UpdateExistingBotLogin(uidFrom, imei, sessionCookies):
    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {})
    if not isinstance(dataBot, dict):
        return None, None, None

    loginFile = dataBot.get(str(uidFrom))
    if not loginFile:
        return None, None, None

    loginPath = os.path.join(os.path.dirname(mainLogin), "multibot", loginFile)
    items = ReadLoginJson(loginPath)
    if not isinstance(items, list) or not items:
        return None, None, None

    bot = items[0] if isinstance(items[0], dict) else None
    if not bot:
        return None, None, None

    bot["imei"] = imei
    bot["sessionCookies"] = sessionCookies

    with open(loginPath, "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=4))

    return bot, loginPath, items

def SaveBotField(fp, items, bot, k, v):
    bot[k] = v
    with open(fp, "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=4))

def DeleteBot(bot, filePath):
    try:
        if filePath == mainLogin:
            return False
        if os.path.exists(filePath):
            os.remove(filePath)
        dataConfig = jsonLoader(mainLogin) or {}
        dataBot = dataConfig.get("dataBot", {})
        for k, v in list(dataBot.items()):
            if v == os.path.basename(filePath):
                del dataBot[k]
        dataConfig["dataBot"] = dataBot
        saveJson(mainLogin, dataConfig)
        return True
    except:
        return False

def restartABot(bot):
    # Placeholder - actual restart logic
    pass

def shutdownABot(bot):
    # Placeholder - actual shutdown logic
    pass

def StopBot(bot, fp, items):
    bot["status"] = False
    if isinstance(fp, str) and fp.endswith(".json"):
        if fp == mainLogin:
            dataConfig = jsonLoader(mainLogin) or {}
            bots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []
            for b in bots:
                if b.get("botIntId") == bot.get("botIntId"):
                    b["status"] = False
            dataConfig["data"] = bots
            saveJson(mainLogin, dataConfig)
        else:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(json.dumps(items, ensure_ascii=False, indent=4))
    shutdownABot(bot)

def ActiveBot(bot, fp, items, timeExpr):
    now = datetime.now()
    expireDelta = ParseTimeExpression(timeExpr)
    expireTime = now + expireDelta

    bot["status"] = True
    bot["isActived"] = True
    bot["activedTime"] = now.strftime("%H:%M:%S-%d/%m/%Y")
    bot["expiredTime"] = expireTime.strftime("%H:%M:%S-%d/%m/%Y")

    if fp == mainLogin:
        dataConfig = jsonLoader(mainLogin) or {}
        bots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []
        for b in bots:
            if b.get("botIntId") == bot.get("botIntId"):
                b.update(bot)
        dataConfig["data"] = bots
        saveJson(mainLogin, dataConfig)
    else:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(json.dumps(items, ensure_ascii=False, indent=4))

    restartABot(bot)

# ============================================================
# COMMAND HANDLERS (ĐÃ FIX)
# ============================================================

def BotManagerCommand(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = (message or "").strip().split()
        cmdb = f"{PREFIX}mybot"
        
        is_main_bot = hasattr(client, 'mainBot') and client.mainBot
        
        if len(parts) < 2:
            if is_main_bot:
                _reply(client, message_object, thread_id, thread_type,
                    f"""
1. Create applications
{cmdb} create IMEI Session Cookies: Create with imei and cookies
{cmdb} create qr: Create with QR Code

2. Manager your applications:
{cmdb} list: All bots
{cmdb} info: Get Info
{cmdb} restart: Restart your BOT
{cmdb} stop: Stop your BOT
{cmdb} prefix: Set bot prefix
{cmdb} server: Get appServer
{cmdb} login: Set login type

3. Management for main
type {cmdb} manager.
    """, sty_info)
            else:
                _reply(client, message_object, thread_id, thread_type,
                    f"""Applications: {getattr(client, 'bot', 'Unknown')}
{cmdb} info: Get Info
{cmdb} restart: Restart your BOT
{cmdb} stop: Stop your BOT
{cmdb} prefix: Set bot prefix
{cmdb} server: Get appServer
{cmdb} login: Set login type
""", sty_info)
            return

        cmd = parts[1].lower()
        isMain = IsMainBotUser(author_id)
        hasMention = bool(GetMentionUid(message_object))
        token = parts[2] if len(parts) > 2 else None

        # ===== FIX: Chỉ chặn delete và group =====
        if cmd in ("delete", "group") and not is_main_bot:
            _reply(client, message_object, thread_id, thread_type,
                "Permission denied, only server main.Bot%", sty_err)
            return

        if cmd == "manager":
            if not is_main_bot:
                _reply(client, message_object, thread_id, thread_type,
                    f"Only server can use {getattr(client, 'rawCommand', 'mybot')}..!", sty_warn)
                return
            manager = f"""{getattr(client, 'bot', 'Bot')} Manager [Server]
    Set GROUP to get login status: {cmdb} group set
    Set send login status: {cmdb} group notify
    Delete userBot: {cmdb} delete [Target]
    Main can target a BOT with mentions or choose index of that BOT
"""
            _reply(client, message_object, thread_id, thread_type, manager, sty_info)
            return

        if cmd == "prefix":
            args = [x for x in parts[2:] if x != "|"]
            if is_main_bot:
                token = args[0] if (hasMention or (args and args[0].isdigit())) else None
                newPrefix = args[1] if token and len(args) >= 2 else (args[0] if args else None)
                if not newPrefix:
                    _reply(client, message_object, thread_id, thread_type,
                        "Set the prefix below the command!", sty_err)
                    return

                if token:
                    bot, fp, items = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token)
                    if not bot:
                        return
                    SaveBotField(fp, items, bot, "prefix", newPrefix)
                    _reply(client, message_object, thread_id, thread_type,
                        f"Updated prefix: {newPrefix}", sty_ok)
                    return

                bot, fp, items = GetOwnBotByFilePath(client)
                if not bot:
                    bot, fp, items = GetOwnBot(client, message_object, author_id, thread_id, thread_type)
                if not bot:
                    _reply(client, message_object, thread_id, thread_type,
                        "Cannot resolve this bot", sty_err)
                    return

                SaveBotField(fp, items, bot, "prefix", newPrefix)
                _reply(client, message_object, thread_id, thread_type,
                    f"Updated prefix: {newPrefix}", sty_ok)
                return

            bot, fp, items = GetOwnBotByFilePath(client)
            if not bot:
                bot, fp, items = GetOwnBot(client, message_object, author_id, thread_id, thread_type)
            if not bot:
                _reply(client, message_object, thread_id, thread_type,
                    "Cannot resolve this bot", sty_err)
                return

            newPrefix = args[0] if args else None
            if not newPrefix:
                _reply(client, message_object, thread_id, thread_type,
                    f"Usage: {cmdb} prefix [Prefix]", sty_err)
                return

            SaveBotField(fp, items, bot, "prefix", newPrefix)
            _reply(client, message_object, thread_id, thread_type,
                f"Updated prefix: {newPrefix}", sty_ok)
            return

        if cmd == "server":
            _reply(client, message_object, thread_id, thread_type,
                getattr(client, 'appServer', 'Unknown'), sty_ok)
            return

        if cmd == "login":
            if len(parts) < 3:
                _reply(client, message_object, thread_id, thread_type,
                    "Set a login type: web or pc", sty_err)
                return

            loginType = (parts[2] or "").lower()
            if loginType not in ("web", "pc"):
                _reply(client, message_object, thread_id, thread_type,
                    "Type support: web and pc", sty_err)
                return

            loginValue = 30 if loginType == "web" else 24

            if is_main_bot:
                token = parts[3] if len(parts) > 3 else None
                if not token and not hasMention:
                    _reply(client, message_object, thread_id, thread_type,
                        "Target a bot to set login type", sty_err)
                    return

                bot, fp, items = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token)
                if not bot:
                    return
                SaveBotField(fp, items, bot, "login", loginValue)
                _reply(client, message_object, thread_id, thread_type,
                    f"Updated login type: {loginType.upper()} for {bot.get('username')}", sty_ok)
                return

            bot, fp, items = GetOwnBotByFilePath(client)
            if not bot:
                bot, fp, items = GetOwnBot(client, message_object, author_id, thread_id, thread_type)
            if not bot:
                _reply(client, message_object, thread_id, thread_type,
                    "Cannot resolve this bot", sty_err)
                return

            SaveBotField(fp, items, bot, "login", loginValue)
            _reply(client, message_object, thread_id, thread_type,
                f"Updated login type: {loginType.upper()}", sty_ok)
            restartABot(bot)
            return

        if cmd == "info":
            if is_main_bot:
                if len(parts) >= 3 or hasMention:
                    bot, fp, _ = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token)
                    if not bot:
                        return
                    if fp == mainLogin or bot.get("mainBot"):
                        _reply(client, message_object, thread_id, thread_type,
                            "@getServerInfo\n<response[0] main.Bot%>", sty_info)
                        return
                    info = f"""@getBotInfo:

:name {bot.get('username', 'Unknown')}
:userclient {bot.get('userClientId') or bot.get('clientBotId') or 'None'}
:socketid {bot.get('botIntId') or 'None'}
:prefix {bot.get('prefix') or 'None'}
:expiredtime {bot.get('expiredTime') or 'None'}
:activedtime {bot.get('activedTime') or 'None'}

@status: {'True' if bot.get('status') else 'False'}"""
                    _reply(client, message_object, thread_id, thread_type, info, sty_info)
                    return
                _reply(client, message_object, thread_id, thread_type,
                    "@getServerInfo\n<response[0] main.Bot%>", sty_info)
                return

            bot, fp, _ = GetOwnBotByFilePath(client)
            if not bot:
                bot, fp, _ = GetOwnBot(client, message_object, author_id, thread_id, thread_type)
            if not bot:
                _reply(client, message_object, thread_id, thread_type,
                    "Cannot resolve this bot", sty_err)
                return
            if fp == mainLogin or bot.get("mainBot"):
                _reply(client, message_object, thread_id, thread_type,
                    "@getServerInfo\n<response[0] main.Bot%>", sty_info)
                return
            info = f"""@getBotInfo:

:name {bot.get('username', 'Unknown')}
:userclient {bot.get('userClientId') or bot.get('clientBotId') or 'None'}
:socketid {bot.get('botIntId') or 'None'}
:prefix {bot.get('prefix') or 'None'}
:expiredtime {bot.get('expiredTime') or 'None'}
:activedtime {bot.get('activedTime') or 'None'}

@status: {'True' if bot.get('status') else 'False'}"""
            _reply(client, message_object, thread_id, thread_type, info, sty_info)
            return

        if not is_main_bot and cmd in ("restart", "stop"):
            bot, fp, items = GetOwnBotByFilePath(client)
            if not fp:
                _reply(client, message_object, thread_id, thread_type,
                    "Missing this filePath in basement", sty_err)
                return
            if not bot:
                _reply(client, message_object, thread_id, thread_type,
                    "Cannot resolve this bot in login file", sty_err)
                return

            if cmd == "stop":
                StopBot(bot, fp, items)
                _reply(client, message_object, thread_id, thread_type,
                    "Your bot has been stopped", sty_ok)
                return

            bot["status"] = True
            if isinstance(fp, str) and fp.endswith(".json") and fp != mainLogin:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(json.dumps(items, ensure_ascii=False, indent=4))
            restartABot(bot)
            _reply(client, message_object, thread_id, thread_type,
                "Restarted your bot..!", sty_ok)
            return

        if cmd == "create":
            # QR Code
            if len(parts) > 2 and parts[2].lower() == "qr":
                _reply(client, message_object, thread_id, thread_type,
                    "QR Code creation...", sty_info)
                return
            
            # Create bot với IMEI và Cookies
            if len(parts) < 4:
                SendMention(client, f"Please type {cmdb} create with IMEI and Session Cookies to GET Login", author_id, thread_id, thread_type)
                return
            
            uidFrom = GetUidFrom(message_object)
            if not uidFrom:
                SendMention(client, "status:null", author_id, thread_id, thread_type)
                return

            imei = parts[2]
            payload = ExtractJsonPayload(" ".join(parts[3:]))
            if not payload:
                SendMention(client, "Invalid cookies JSON", author_id, thread_id, thread_type)
                return
            
            try:
                sessionCookies = json.loads(payload)
            except:
                SendMention(client, "Invalid cookies JSON", author_id, thread_id, thread_type)
                return

            # Kiểm tra đã có bot chưa
            bot, _, _ = UpdateExistingBotLogin(uidFrom, imei, sessionCookies)
            if bot:
                SendMention(client, f"Updated IMEI & Cookies for {bot.get('username')}", author_id, thread_id, thread_type)
                return

            # Tạo bot mới
            dataConfig = jsonLoader(mainLogin) or {}
            dataBot = dataConfig.get("dataBot", {}) if isinstance(dataConfig.get("dataBot", {}), dict) else {}
            username = f"{client.userName(uidFrom)}-{len(dataConfig.get('data', []))}"
            prefixList = ["/", ".", "_", "-", ",", ">", "<", ")", "(", "~", "[", "]", ";"]
            prefix = random.choice(prefixList)
            botAccount = SlugName(client.userName(uidFrom))
            botPassword = str(random.randint(100000, 999999))

            newBot = {
                "username": username,
                "login": 24,
                "botIntId": str(author_id),
                "imei": imei,
                "prefix": prefix,
                "sessionCookies": sessionCookies,
                "clientBotId": str(uidFrom),
                "mainBot": False,
                "status": False,
                "isActived": False,
                "botAccount": botAccount,
                "botPassword": botPassword
            }

            multibot_dir = os.path.join(os.path.dirname(mainLogin), "multibot")
            os.makedirs(multibot_dir, exist_ok=True)
            indexFile = 1
            while os.path.exists(os.path.join(multibot_dir, f"{indexFile}-login.json")):
                indexFile += 1

            loginFile = f"{indexFile}-login.json"
            loginPath = os.path.join(multibot_dir, loginFile)

            with open(loginPath, "w", encoding="utf-8") as f:
                json.dump([newBot, {"userClientId": str(uidFrom)}], f, ensure_ascii=False, indent=4)

            dataBot[str(uidFrom)] = loginFile
            dataConfig["dataBot"] = dataBot
            saveJson(mainLogin, dataConfig)

            SendMention(client, f"[{prefix}] Successful create {client.userName(uidFrom)} BOT..", author_id, thread_id, thread_type)
            
            # Gửi thông tin login
            try:
                app_server = getattr(client, 'appServer', 'Unknown')
                login_msg = f"""✅ TẠO BOT THÀNH CÔNG!

🔗 Web Server: {app_server}
👤 Account: {botAccount}
🔑 Password: {botPassword}

💡 Dùng thông tin trên để đăng nhập bot!
"""
                client.sendMessage(Message(text=login_msg), author_id, ThreadType.USER)
            except:
                pass
            return

        if cmd == "list":
            arr = BuildBotIndexList()
            if not arr:
                SendMention(client, "No bots found", author_id, thread_id, thread_type)
                return

            now = datetime.now()

            def ParseTime(s):
                try:
                    return datetime.strptime(str(s), "%H:%M:%S-%d/%m/%Y")
                except:
                    return None

            def StatusText(b):
                if "isActived" not in b:
                    return "Non Active"
                exp = ParseTime(b.get("expiredTime"))
                if exp and now > exp:
                    return "Expired"
                return "Active" if b.get("status") else "Inactive"

            out = "All bots on server:\n"
            for i, (b, _, __) in enumerate(arr, 1):
                if not isinstance(b, dict):
                    continue
                if b.get("mainBot"):
                    continue

                st = StatusText(b)
                out += f"{i}. {b.get('username')}{f' - {st}' if st else ''}\n"
                out += f"   botIntId: {b.get('botIntId')}\n"
                out += f"   Prefix: {b.get('prefix')}\n"
                if b.get("expiredTime"):
                    out += f"   Expires: {b.get('expiredTime')}\n"

            SendMention(client, out, author_id, thread_id, thread_type)
            return

        if cmd == "group":
            if not isMain:
                _reply(client, message_object, thread_id, thread_type,
                    "Permission denied", sty_err)
                return

            sub = parts[2].lower() if len(parts) > 2 else ""
            if sub == "set":
                _reply(client, message_object, thread_id, thread_type,
                    "Group link set", sty_info)
                return

            if sub == "notify":
                cfg = loadBotManager()
                dg = dataGroup(cfg)
                cur = dg.get("sendNotify")
                dg["sendNotify"] = False if cur is True else True
                botManagerSave(cfg)
                _reply(client, message_object, thread_id, thread_type,
                    f"sendNotify: {dg['sendNotify']}", sty_info)
                return

            _reply(client, message_object, thread_id, thread_type,
                "...", sty_warn)
            return

        if cmd == "update":
            if not isMain:
                _reply(client, message_object, thread_id, thread_type,
                    "Only mainBot can update the bot..!", sty_err)
                return
            if len(parts) < 4 and not hasMention:
                _reply(client, message_object, thread_id, thread_type,
                    "Which bot will update?", sty_err)
                return
            _reply(client, message_object, thread_id, thread_type,
                "Update login...", sty_info)
            return

        if cmd == "changeowner":
            if not isMain:
                _reply(client, message_object, thread_id, thread_type,
                    "Permission denied", sty_err)
                return
            _reply(client, message_object, thread_id, thread_type,
                "Change owner...", sty_info)
            return

        if cmd == "start":
            if not isMain:
                if len(parts) != 2:
                    return
                bot, fp, items = GetOwnBot(client, message_object, author_id, thread_id, thread_type)
                if not bot or not bot.get("expiredTime"):
                    return
                bot["status"] = True
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(json.dumps(items, ensure_ascii=False, indent=4))
                restartABot(bot)
                _reply(client, message_object, thread_id, thread_type,
                    "Bot has been started", sty_ok)
                return

            if len(parts) < 4 and not hasMention:
                _reply(client, message_object, thread_id, thread_type,
                    "Target a bot to start and set time", sty_err)
                return
            timeExpr = parts[-1]
            bot, fp, items = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token if len(parts) > 3 else None)
            if not bot:
                return
            ActiveBot(bot, fp, items, timeExpr)
            _reply(client, message_object, thread_id, thread_type,
                f"Activated {bot.get('activedTime')} until {bot.get('expiredTime')} will expire..!", sty_ok)
            return

        if cmd == "restart":
            if len(parts) < 3 and not hasMention:
                _reply(client, message_object, thread_id, thread_type,
                    "Target a bot to restart", sty_err)
                return
            bot, fp, items = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token)
            if not bot:
                return
            bot["status"] = True
            if isinstance(fp, str) and fp.endswith(".json") and fp != mainLogin:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(json.dumps(items, ensure_ascii=False, indent=4))
            restartABot(bot)
            _reply(client, message_object, thread_id, thread_type,
                f"Restarted {bot.get('username')}", sty_ok)
            return

        if cmd == "stop":
            if len(parts) < 3 and not hasMention:
                _reply(client, message_object, thread_id, thread_type,
                    "Target a bot to stop", sty_err)
                return
            bot, fp, items = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token)
            if not bot:
                return
            StopBot(bot, fp, items)
            _reply(client, message_object, thread_id, thread_type,
                "Stopped", sty_ok)
            return

        if cmd == "delete":
            if len(parts) < 3 and not hasMention:
                _reply(client, message_object, thread_id, thread_type,
                    "Which one will bye the server?", sty_err)
                return
            bot, fp, _ = GetBotByIndexOrMention(client, message_object, author_id, thread_id, thread_type, token)
            if not bot:
                return
            if fp == mainLogin:
                _reply(client, message_object, thread_id, thread_type,
                    "Cannot delete main bot", sty_err)
                return
            if not DeleteBot(bot, fp):
                _reply(client, message_object, thread_id, thread_type,
                    "Delete failed", sty_err)
                return
            _reply(client, message_object, thread_id, thread_type,
                "Bot deleted from the system", sty_ok)
            return

        return

    except Exception as e:
        _reply(client, message_object, thread_id, thread_type,
            f"Error: {str(e)}", sty_err)

# ============================================================
# LOAD
# ============================================================

def Kryzis():
    return {'mybot': BotManagerCommand}