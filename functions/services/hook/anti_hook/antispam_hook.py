from dto.index import *

def _NormObjContent(v):
    try:
        if v is None:
            return ""
        if isinstance(v, (str, int, float, bool)):
            return str(v).strip()
        if isinstance(v, bytes):
            try:
                return v.decode("utf-8", "ignore").strip()
            except:
                return ""
        if isinstance(v, dict):
            for k in ("title", "text", "caption", "description", "message"):
                if k in v and v.get(k):
                    return str(v.get(k)).strip()
            x = dict(v)
            for k in ("timestamp", "id", "time", "date", "ts", "cliMsgId", "msgId"):
                if k in x:
                    x.pop(k, None)
            return json.dumps(x, ensure_ascii=False, separators=(",", ":"))
        if isinstance(v, (list, tuple)):
            return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        return str(v).strip()
    except:
        return ""

def _LevDist(a, b):
    if a == b:
        return 0
    la = len(a)
    lb = len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    if la < lb:
        a, b = b, a
        la, lb = lb, la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        ca = a[i - 1]
        cur = [i]
        pj = prev
        for j in range(1, lb + 1):
            cost = 0 if ca == b[j - 1] else 1
            cur.append(min(pj[j] + 1, cur[j - 1] + 1, pj[j - 1] + cost))
        prev = cur
    return prev[lb]

def _Similarity(a, b):
    try:
        if not isinstance(a, str) or not isinstance(b, str):
            return 0.0
        a = a.lower().strip()
        b = b.lower().strip()
        if a == b:
            return 1.0
        ml = max(len(a), len(b))
        if ml == 0:
            return 1.0
        d = _LevDist(a, b)
        return 1.0 - (d / ml)
    except:
        return 0.0

def _SpamReason(spamType):
    if spamType == "RAPID_MESSAGES":
        return "send rapid messages"
    if spamType == "BURST_MESSAGES":
        return "spam burst"
    if spamType == "REPEATED_CONTENT":
        return "repeat spam"
    if spamType == "BULK_MESSAGES":
        return "send many bulk messages in a time"
    return "spam"

def _AnalyzeSpam(msgs, now, rapidCount=5, rapidWindow=3.0, burstCount=4, burstWindow=1.2, repeatCount=4, repeatWindow=6.0, longCount=2, longLen=120, longWindow=3.0, simTh=0.86):
    r = [m for m in msgs if now - m["t"] <= rapidWindow]
    if len(r) >= rapidCount:
        if r[-1]["t"] - r[0]["t"] <= rapidWindow:
            return True, "RAPID_MESSAGES"

    b = [m for m in msgs if now - m["t"] <= burstWindow]
    if len(b) >= burstCount:
        return True, "BURST_MESSAGES"

    rep = [m for m in msgs if now - m["t"] <= repeatWindow]
    contentMap = []
    for m in rep:
        c = m.get("c", "")
        s = c if isinstance(c, str) else _NormObjContent(c)
        s = (s or "").strip()
        if not s:
            continue
        hit = False
        for i in range(len(contentMap)):
            if _Similarity(s, contentMap[i][0]) >= simTh:
                contentMap[i][1] += 1
                if contentMap[i][1] >= repeatCount:
                    return True, "REPEATED_CONTENT"
                hit = True
                break
        if not hit:
            contentMap.append([s, 1])

    lw = [m for m in msgs if now - m["t"] <= longWindow]
    lc = 0
    for m in lw:
        if (m.get("l", 0) or 0) >= longLen:
            lc += 1
            if lc >= longCount:
                return True, "BULK_MESSAGES"

    return False, ""

def _WarnKey(threadId, userId):
    return (str(threadId), str(userId))

def _IsKicked(this, key, now):
    if not hasattr(this, "_antiSpamKicked"):
        this._antiSpamKicked = {}
    t = this._antiSpamKicked.get(key)
    if not t:
        return False
    if now - t > 6.0:
        this._antiSpamKicked.pop(key, None)
        return False
    return True

def _MarkKicked(this, key, now):
    if not hasattr(this, "_antiSpamKicked"):
        this._antiSpamKicked = {}
    this._antiSpamKicked[key] = now

def _WarnStateGet(this, key, now):
    if not hasattr(this, "_antiSpamWarn"):
        this._antiSpamWarn = {}
    w = this._antiSpamWarn.get(key)
    if not w:
        w = {"count": 0, "last": now}
        this._antiSpamWarn[key] = w
        return w
    resetTime = 1800.0
    dec = int((now - (w.get("last") or now)) // resetTime)
    if dec > 0:
        w["count"] = max(0, int(w.get("count") or 0) - dec)
        w["last"] = now
        if w["count"] <= 0:
            this._antiSpamWarn.pop(key, None)
            w = {"count": 0, "last": now}
            this._antiSpamWarn[key] = w
    return w

def _WarnAndCheck(this, key, now):
    w = _WarnStateGet(this, key, now)
    w["count"] = int(w.get("count") or 0) + 1
    w["last"] = now
    if w["count"] >= 3:
        this._antiSpamWarn.pop(key, None)
        return True, 3
    return False, w["count"]

def antiSpamMessage(this, message, data, userId, threadId, type):
    if data.msgType == "chat.reaction":
        return
    if not hasattr(this, "_antiSpamLog"):
        this._antiSpamLog = {}
    if not hasattr(this, "_antiSpamMsgIds"):
        this._antiSpamMsgIds = {}

    settings = ReadServices(this.uid)
    antiSpam = settings.get("antiSpam", [])
    if threadId not in antiSpam:
        return

    grInfo = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
    adminIds = grInfo.get("adminIds", [])
    creatorId = grInfo.get("creatorId")

    if this.uid not in adminIds and this.uid != creatorId:
        return

    if userId == creatorId or userId in adminIds:
        return

    if skip(this, userId, threadId):
        return

    now = time.time()
    wk = _WarnKey(threadId, userId)
    if _IsKicked(this, wk, now):
        return

    key = (threadId, userId)

    c = getattr(data, "content", None)
    norm = _NormObjContent(c)
    ln = 0
    try:
        ln = len(norm)
    except:
        ln = 0

    logs = this._antiSpamLog.get(key, [])
    logs = [m for m in logs if now - m["t"] <= 8.0]
    logs.append({"t": now, "c": c, "l": ln})
    this._antiSpamLog[key] = logs

    msgIds = this._antiSpamMsgIds.get(key, [])
    msgIds = [x for x in msgIds if now - x["t"] <= 12.0]
    try:
        msgIds.append({"t": now, "msgId": data.msgId, "cliMsgId": data.cliMsgId, "uidFrom": data.uidFrom})
    except:
        pass
    this._antiSpamMsgIds[key] = msgIds

    isSpam, spamType = _AnalyzeSpam(
        logs,
        now,
        rapidCount=5,
        rapidWindow=3.0,
        burstCount=4,
        burstWindow=1.2,
        repeatCount=4,
        repeatWindow=6.0,
        longCount=2,
        longLen=120,
        longWindow=3.0,
        simTh=0.86
    )
    if not isSpam:
        return

    try:
        this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)
    except:
        pass

    shouldBlock, warnCount = _WarnAndCheck(this, wk, now)
    if not shouldBlock:
        try:
            cap = "Chill nah broooooo.. Slowly, u seem likes a spammers"
            if warnCount == 2:
                cap = "Stop spamming, or you will get my gift..!"
            this.sendMWarning(cap, userId, threadId, type)
        except:
            pass
        return

    _MarkKicked(this, wk, now)

    try:
        reason = _SpamReason(spamType)
        this.sendMWarning(f"Blocked by {reason}!", userId, threadId, type)
    except:
        pass

    try:
        for x in this._antiSpamMsgIds.get(key, [])[-20:]:
            try:
                this.deleteMessage(x.get("msgId"), x.get("uidFrom"), x.get("cliMsgId"), threadId)
            except:
                pass
    except:
        pass

    try:
        this.blockUsers(userId, threadId)
    except:
        pass

    this._antiSpamLog.pop(key, None)
    this._antiSpamMsgIds.pop(key, None)