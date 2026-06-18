from app.library.packages import *
from functions.engine.data.data import ReadServices, jsonLoader, saveJson

def doneRestart(this):
    data = jsonLoader(tempPath, {})
    user = data.get("user")
    threadId = data.get("thread")
    this.sendMSuccess("Successful started system again", user, threadId, type=ThreadType.GROUP)
    data.pop("thread", None)
    data.pop("user", None)
    saveJson(tempPath, data)

def getAllowed(this):
    settings = ReadServices(this.uid)
    return settings.get("allowGroup", [])