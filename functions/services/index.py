from app.core.login.start import *
from app.core.login.client import getClient
from dto.index import *

def _GetTarget(botIntId, isMain):
    if isMain:
        e = getClient.getMain()
        return e.client if e else None
    e = getClient.get(botIntId)
    return e.client if e else None

def restartABot(bot):
    username = bot.get("username")
    botIntId = str(bot.get("botIntId"))
    imei = bot.get("imei")
    cookies = bot.get("sessionCookies")
    prefix = bot.get("prefix", "?")
    isMain = bot.get("mainBot", False)
    status = bot.get("status", False)
    filePath = bot.get("filePath")
    loginType = bot.get("login")

    target = _GetTarget(botIntId, isMain)
    if target and hasattr(target, "stopListening"):
        try:
            target.stopListening()
            time.sleep(0.8)
        except:
            pass

    RunBot(imei, cookies, prefix, isMain, username, botIntId, status, filePath, loginType)

def shutdownABot(bot):
    username = bot.get("username")
    botIntId = str(bot.get("botIntId"))
    isMain = bot.get("mainBot", False)

    target = _GetTarget(botIntId, isMain)
    if target and hasattr(target, "stopListening"):
        try:
            target.stopListening()
            time.sleep(0.8)
        except Exception as e:
            logger.warning(f"Lỗi stop bot {username}: {e}")
