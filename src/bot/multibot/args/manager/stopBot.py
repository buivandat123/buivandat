from functions.services.hook.core_hook.extra_multibot_core import *

def StopBot(this, bot, filePath, items):
    bot["status"] = False
    if isinstance(filePath, str) and filePath.endswith(".json"):
        if filePath == mainLogin:
            dataConfig = jsonLoader(mainLogin) or {}
            bots = dataConfig.get("data", []) if isinstance(dataConfig.get("data", []), list) else []
            for b in bots:
                if b.get("botIntId") == bot.get("botIntId"):
                    b["status"] = False
            dataConfig["data"] = bots
            saveJson(mainLogin, dataConfig)
        else:
            with open(filePath, "w", encoding="utf-8") as f:
                f.write(json.dumps(items, ensure_ascii=False, indent=4))
    shutdownABot(bot)