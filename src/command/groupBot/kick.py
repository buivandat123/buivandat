from dto.index import *

def CleanMemVerList(memVerList):
    out = []
    for x in memVerList or []:
        if not x:
            continue
        if isinstance(x, str):
            if x.endswith("_0"):
                x = x[:-2]
        out.append(str(x))
    seen = set()
    return [v for v in out if v not in seen and not seen.add(v)]

def KickCommand(this, message, data, userId, threadId, type):
    text = (getattr(message, "text", None) or "").strip()
    parts = text.split()
    sub = (parts[1].lower() if len(parts) > 1 else "")

    quote = getattr(data, "quote", None)
    uids = this.extractUids(data) or []

    if sub == "all":
        info = this.fetchGroupInfo(threadId).gridInfoMap.get(str(threadId)) or this.fetchGroupInfo(threadId).gridInfoMap.get(threadId) or {}
        memList = CleanMemVerList(info.get("memVerList"))
        adminIds = {str(x) for x in (info.get("adminIds") or []) if x}
        creatorId = str(info.get("creatorId") or "")
        botId = str(getattr(this, "uid", "") or getattr(getattr(this, "user", None), "id", "") or "")

        protect = {str(userId), botId, creatorId} | adminIds
        targets = [x for x in memList if x and x not in protect]

        if not targets:
            return this.sendMFailed("No members to kick..!", userId, threadId, type)

    else:
        if not quote and not uids:
            return this.sendMWarning("Please quote a message of user or mention..!", userId, threadId, type)

        targets = uids if uids else [getattr(quote, "ownerId", None)]
        seen = set()
        targets = [str(x) for x in targets if x and (str(x) not in seen and not seen.add(str(x)))]

        if not targets:
            return this.sendMFailed("Can only kick members..!", userId, threadId, type)
    this.kickUsers(targets, threadId)

dependencies = {
    "name": "kick",
    "permission": 1,
    "description": "Kick a member | kick all",
    "cooldown": 5,
    "main": KickCommand
}