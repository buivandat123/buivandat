from dto.index import *

def hideMessage(this, message, data, userId, threadId, type):
    parts = (message.text or "").split()
    if len(parts) < 3:
        return this.sendMWarning(f"use {this.rawCommand} and message with count and time to sleep", userId, threadId, type)

    sleep = 1.0
    if len(parts) >= 4:
        try:
            sleep = float(parts[-1])
        except:
            sleep = 1.0

    try:
        count = int(parts[-2])
    except:
        return this.sendMWarning("Count must be number", userId, threadId, type)

    messager = " ".join(parts[1:-2]).strip()
    if not messager:
        return this.sendMFailed("Message empty", userId, threadId, type)

    originalMessage = this.sendMessage(Message(text=messager), threadId, type)

    for _ in range(count):
        time.sleep(sleep)
        this.sendMessageByCliMsgId(Message(text=messager), threadId, type, originalMessage.clientId)

dependencies = {
    "name": "hide",
    "permission": 3,
    "description": "No Description",
    "cooldown": 5,
    "main": hideMessage
}