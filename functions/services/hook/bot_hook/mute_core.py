from dto.index import *

def parseDuration(parts):
    if not parts:
        return None, None
    last = parts[-1].lower()
    if last in ("inf", "infinite", "forever"):
        return 0, "inf"
    m = re.match(r"^(\d+)(s|sec|secs|m|min|mins|h|hr|hrs|d|day|days|w|week|weeks)$", last)
    if m:
        v = int(m.group(1))
        u = m.group(2)
        return changeSecond(v, u), f"{v}{u}"
    if len(parts) >= 2 and parts[-1].lower() in ("s","sec","secs","m","min","mins","h","hr","hrs","d","day","days","w","week","weeks") and parts[-2].isdigit():
        v = int(parts[-2])
        u = parts[-1].lower()
        return changeSecond(v, u), f"{v}{u}"
    return None, None

def changeSecond(v, u):
    if u in ("s","sec","secs"):
        return v
    if u in ("m","min","mins"):
        return v * 60
    if u in ("h","hr","hrs"):
        return v * 3600
    if u in ("d","day","days"):
        return v * 86400
    if u in ("w","week","weeks"):
        return v * 604800
    return v

def formatRemaining(untilTs):
    if not untilTs:
        return "inf"
    left = int(untilTs - time.time())
    if left <= 0:
        return "0s"
    if left < 60:
        return f"{left}s"
    if left < 3600:
        return f"{left//60}m"
    if left < 86400:
        return f"{left//3600}h"
    return f"{left//86400}d"

def silentListener(this, message, data, userId, threadId, type):
    if not hasattr(this, "_silentCount"):
        this._silentCount = {}

    s = ReadServices(this.uid)
    isAll = bool((s.get("isSlientAll", {}) or {}).get(str(threadId)))
    silentMap = (((s.get("silent", {}) or {}).get("group", {}) or {}).get(str(threadId), {}) or {})

    now = time.time()
    if isAll:
        blocked = True
    else:
        meta = silentMap.get(str(userId))
        if not meta:
            return
        untilTs = meta.get("until", 0)
        if untilTs and untilTs <= now:
            silentMap.pop(str(userId), None)
            s.setdefault("silent", {}).setdefault("group", {}).setdefault(str(threadId), {})
            s["silent"]["group"][str(threadId)] = silentMap
            WriteService(this.uid, s)
            return
        blocked = True

    if not blocked:
        return

    key = (threadId, userId)
    this._silentCount[key] = this._silentCount.get(key, 0) + 1
    this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)