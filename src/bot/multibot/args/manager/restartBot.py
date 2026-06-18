from functions.services.hook.core_hook.extra_multibot_core import *

def RestartBot(this, bot, filePath, items):
    bot["status"] = True
    if isinstance(filePath, str) and filePath.endswith(".json") and filePath != mainLogin:
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(json.dumps(items, ensure_ascii=False, indent=4))
    restartABot(bot)