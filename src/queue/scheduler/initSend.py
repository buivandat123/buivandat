from functions.services.init.sendTime import *

def initSend(this, message, data, userId, threadId, type):
    s, state, threads, _, lastSent = getSendState(this.uid)

    if type.name == "USER":
        return

    if threadId in threads:
        threads.remove(threadId)
    else:
        threads.append(threadId)

    saveSendState(this.uid, s, state, threads, lastSent)
    return this.sendMSuccess(
        f"Auto send {'on' if threadId in threads else 'off'} for this {this.groupHub(threadId)}",
        userId,
        threadId,
        type
    )

dependencies = {
    "name": "autosend",
    "permission": 2,
    "description": "Automation sending",
    "cooldown": 5,
    "main": initSend
}