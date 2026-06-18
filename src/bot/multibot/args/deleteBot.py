from functions.services.hook.core_hook.extra_multibot_core import *

def DeleteBot(this, bot, filePath):
    try:
        shutdownABot(bot)

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
    except Exception as e:
        logger.errorMeta(f"DeleteBot error: {e}")
        return False