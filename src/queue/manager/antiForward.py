from dto.index import *
def isForwardMessage(data):
    try:
        ref = getattr(data, "reference", None)
        if not ref:
            return False

        raw = ref.get("data")
        if not raw:
            return False

        refData = json.loads(raw)
        return bool(refData.get("fwLvl"))
    except:
        return False
def antiForwardCommand(this, message, data, userId, threadId, type):
    parts = message.text.strip().split()

    settings = ReadServices(this.uid)
    antifw = settings.setdefault("antiForward", [])
    enabled = threadId in antifw

    if len(parts) < 2:
        enabled = not enabled
    else:
        action = parts[1].lower()
        if action == "on":
            enabled = True
        elif action == "off":
            enabled = False
        else:
            return

    if enabled and threadId not in antifw:
        antifw.append(threadId)

    if not enabled and threadId in antifw:
        antifw.remove(threadId)

    WriteService(this.uid, settings)

    status = "enabled" if enabled else "disabled"
    this.sendMSuccess(
        f"Anti forward is now {status}.",
        userId,
        threadId,
        type
    )
def antiForward(this, message, data, userId, threadId, type):
    if not hasattr(this, "_antiForwardCount"):
        this._antiForwardCount = {}

    settings = ReadServices(this.uid)
    antifw = settings.get("antiForward", [])

    if threadId not in antifw:
        return

    grInfo = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
    adminIds = grInfo.get("adminIds", [])
    creatorId = grInfo.get("creatorId")

    if userId == creatorId or userId in adminIds:
        return
    
    if this.uid not in adminIds and this.uid != creatorId:
        return

    if skip(this, userId, threadId):
        return

    if not isForwardMessage(data):
        return

    key = (threadId, userId)
    count = this._antiForwardCount.get(key, 0) + 1
    this._antiForwardCount[key] = count

    try:
        this.deleteMessage(
            data.msgId,
            data.uidFrom,
            data.cliMsgId,
            threadId
        )
    except:
        pass

    if count < 5:
        this.sendMWarning(
            f"Forward messaged is banned in this {this.groupHub(threadId)}, deleted.",
            userId,
            data,
            threadId,
            type
        )
        return

    this.sendMWarning(
        "Forward spam detected. User removed from group.",
        userId,
        data,
        threadId,
        type
    )

    this.blockUsers(userId, threadId)
    this._antiForwardCount.pop(key, None)


dependencies = {
    "name": "antiforward",
    "permission": 2,
    "description": "Anti forward message",
    "cooldown": 5,
    "main": antiForwardCommand
}