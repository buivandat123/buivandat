from functions.services.hook.core_hook.extra_multibot_core import *

def BuildBotInfoText(bot):
    botName = bot.get("username") or bot.get("name") or "Unknown"
    userClient = bot.get("userClientId") or bot.get("clientBotId") or bot.get("clientId") or "None"
    socketId = bot.get("botIntId") or bot.get("socketid") or bot.get("socketId") or "None"
    prefix = bot.get("prefix") or "None"
    et = bot.get("expiredTime") or "None"
    at = bot.get("activedTime") or "None"
    stt = bot.get("status")
    stt = "True" if stt is True else ("False" if stt is False else str(stt))

    return (
        "@getBotInfo:\n\n"
        f":name {botName}\n"
        f":userclient {userClient}\n"
        f":socketid {socketId}\n"
        f":prefix {prefix}\n"
        f":expiredtime {et}\n"
        f":activedtime {at}\n\n"
        f"@status: {stt}"
    )

def TryBuildServerInfoText(this):
    try:
        r = "<response[0] main.Bot%>"
        if isinstance(r, (list, tuple)) and len(r) > 0:
            return f"@getServerInfo\n{r[0]}"
        if isinstance(r, dict):
            v = r.get(0) or r.get("0") or r.get("response") or r.get("data")
            if v is not None:
                return f"@getServerInfo\n{v}"
        if isinstance(r, str) and r.strip():
            return f"@getServerInfo\n{r}"
    except Exception:
        pass
    return "@getServerInfo\nNone"

def IsMainBotTarget(fp, bot):
    try:
        if fp == mainLogin:
            return True
    except Exception:
        pass
    if bot.get("isMain") is True:
        return True
    if bot.get("mainBot") is True:
        return True
    if (bot.get("type") or "").lower() == "main":
        return True
    return False