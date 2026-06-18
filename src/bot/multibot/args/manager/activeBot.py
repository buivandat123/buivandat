from functions.services.hook.core_hook.extra_multibot_core import *

def ActiveBot(this, bot, filePath, items, timeExpr):
    now = datetime.now()
    expireDelta = ParseTimeExpression(timeExpr)
    expireTime = now + expireDelta

    bot["status"] = True
    bot["isActived"] = True
    bot["activedTime"] = now.strftime("%H:%M:%S-%d/%m/%Y")
    bot["expiredTime"] = expireTime.strftime("%H:%M:%S-%d/%m/%Y")

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