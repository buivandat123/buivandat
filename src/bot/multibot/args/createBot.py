from functions.services.hook.core_hook.extra_multibot_core import *

def UpdateExistingBotLogin(uidFrom, imei, sessionCookies):
    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {})
    if not isinstance(dataBot, dict):
        return None, None, None

    loginFile = dataBot.get(str(uidFrom))
    if not loginFile:
        return None, None, None

    loginPath = os.path.join("assets", "config", "multibot", loginFile)
    items = jsonLoader(loginPath)
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

def CreateBot(this, message, data, userId, threadId, type):
    uidFrom = GetUidFrom(data)
    if not uidFrom:
        return SendMention(this, "status:null", userId, threadId, type)

    raw = (message.text or "").strip()
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return SendMention(this, f"Please type {this.prefix}{this.rawCommand} create with IMEI and Session Cookies to GET Login", userId, threadId, type)

    imei = parts[0]
    payload = ExtractJsonPayload(parts[1])
    sessionCookies = json.loads(payload)

    bot, _, _ = UpdateExistingBotLogin(uidFrom, imei, sessionCookies)
    if bot:
        return SendMention(this, f"Updated IMEI & Cookies for {bot.get('username')}", userId, threadId, type)

    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {}) if isinstance(dataConfig.get("dataBot", {}), dict) else {}
    botIntId = str(userId)
    username = f"{this.userName(uidFrom)}-{len(dataConfig.get('data', []))}"
    prefixList = ["/", ".", "_", "-", ",", ">", "<", ")", "(", "~", "[", "]", ";"]
    prefix = random.choice(prefixList)
    botAccount = SlugName(this.userName(uidFrom))
    botPassword = str(this.randomInt())

    newBot = {
        "username": username,
        "login": 24,
        "botIntId": botIntId,
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

    os.makedirs(os.path.join("assets", "config", "multibot"), exist_ok=True)
    indexFile = 1
    while os.path.exists(os.path.join("assets", "config", "multibot", f"{indexFile}-login.json")):
        indexFile += 1

    loginFile = f"{indexFile}-login.json"
    loginPath = os.path.join("assets", "config", "multibot", loginFile)

    with open(loginPath, "w", encoding="utf-8") as f:
        json.dump([newBot, {"userClientId": str(uidFrom)}], f, ensure_ascii=False, indent=4)

    dataBot[str(uidFrom)] = loginFile
    dataConfig["dataBot"] = dataBot
    saveJson(mainLogin, dataConfig)

    SendMention(this, f"[{prefix}] Successful create {this.userName(uidFrom)} BOT..", userId, threadId, type)
    this.sendMention(f"""Web: {this.appServer}
Account: {botAccount}
Password: {botPassword}
""", userId, userId, ThreadType.USER)