from dto.index import *
from functions.services.index import *

def SavePort(p: int):
    try:
        with open(cfgPath, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except:
        data = {}
    data["serverport"] = int(p)
    os.makedirs(os.path.dirname(cfgPath), exist_ok=True)
    with open(cfgPath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def saveTemp(threadId, userId):
    data = jsonLoader(tempPath, {})
    data["thread"] = threadId
    data["user"] = userId
    saveJson(tempPath, data)

def restartCommand(this, message, data, userId, threadId, type):
    if not this.mainBot:
            return this.sendMWarning(
                f"Only server can use {this.rawCommand}..!",
                userId, threadId, type
            )
    p = int(cfgData.get("serverport", 1000))
    saveTemp(threadId, userId)
    p += 1
    SavePort(p)
    this.sendMSuccess("Progress apply, will executable now..!", userId, threadId, type)
    os.execv(sys.executable, [sys.executable] + sys.argv)

dependencies = {
    "name": "restart",
    "permission": 3,
    "description": "Restart bot, program",
    "cooldown": 5,
    "main": restartCommand
}