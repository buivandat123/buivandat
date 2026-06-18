from functions.services.hook.core_hook.extra_multibot_core import *

def UpdateLoginCre(this, message, data, userId, threadId, type):
    raw = (message.text or "").strip()
    parts = raw.split(maxsplit=4)

    if not parts or parts[0].lower() != "update":
        return 

    if this.mainBot:
        if len(parts) < 4:
            return 

        token = parts[1]
        imei = parts[2]
        payload = ExtractJsonPayload(" ".join(parts[3:]))
        if not payload:
            return SendMention(this, "Invalid cookies JSON", userId, threadId, type)

        try:
            sessionCookies = json.loads(payload)
        except Exception:
            return SendMention(this, "Invalid cookies JSON", userId, threadId, type)

        bot, filePath, items = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
        if not bot:
            return

        bot["imei"] = imei
        bot["sessionCookies"] = sessionCookies

        if filePath == mainLogin:
            dataConfig = jsonLoader(mainLogin) or {}
            bots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []
            for b in bots:
                if b.get("botIntId") == bot.get("botIntId"):
                    b.update(bot)
            dataConfig["data"] = bots
            saveJson(mainLogin, dataConfig)
        else:
            with open(filePath, "w", encoding="utf-8") as f:
                f.write(json.dumps(items, ensure_ascii=False, indent=4))

        restartABot(bot)
        return SendMention(this, "Updated", userId, threadId, type)

    if len(parts) < 3:
        return SendMention(this, "Usage: update [imei] [cookiesjson]", userId, threadId, type)

    imei = parts[1]
    payload = ExtractJsonPayload(" ".join(parts[2:]))
    if not payload:
        return SendMention(this, "Invalid cookies JSON", userId, threadId, type)

    try:
        sessionCookies = json.loads(payload)
    except Exception:
        return SendMention(this, "Invalid cookies JSON", userId, threadId, type)

    bot, filePath, items = GetOwnBot(this, data, userId, threadId, type)
    if not bot:
        return

    bot["imei"] = imei
    bot["sessionCookies"] = sessionCookies

    with open(filePath, "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=4))

    restartABot(bot)
    SendMention(this, "Updated", userId, threadId, type)