from dto.index import *
from functions.services.index import *

def checkPrefix(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    if len(parts) < 2:
        return

    newPrefix = parts[-1]
    dataConfig = jsonLoader(mainLogin) or {}
    dataConfig["prefix"] = newPrefix

    saveJson(mainLogin, dataConfig)
    restartABot(this)

    return this.sendMSuccess(
        f"Changed prefix to: {newPrefix}",
        userId, data, threadId, type
    )

dependencies = {
    "name": "prefix",
    "permission": 3,
    "description": "Change prefix",
    "cooldown": 3,
    "main": checkPrefix
}