from dto.index import *

def react(s):
    e, t = [], []
    for c in s:
        (e if c in emoji.EMOJI_DATA else t).append(c)
    return "".join(e), "".join(t).strip()

def detectPlatform(p):
    return {0: "Zalo APP", 1: "Zalo Web", 2: "Zalo PC"}.get(p, "Unknown")

def detectTypeSend(d):
    m = getattr(d, "msgType", "")
    if m == "webchat":
        return "replyMessage" if getattr(d, "quote", None) else "sendMessage"
    return {
        "chat.photo": "sendPhoto",
        "chat.video.msg": "sendVideo",
        "chat.reaction": "sendReaction",
        "chat.recommended": "sendBusinessCard"
    }.get(m, m)

def toDict(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            v = json.loads(x)
            return v if isinstance(v, dict) else {}
        except:
            return {}
    return {}

def mentionsData(d):
    ms = getattr(d, "mentions", None)
    if ms:
        return ms
    return toDict(getattr(d, "attach", None)).get("mentions", [])

def botLogic(this, d):
    s = 0
    uid = str(getattr(d, "uidFrom", ""))
    userId = str(getattr(d, "userId", ""))
    uin = str(getattr(d, "uin", ""))
    m = getattr(d, "msgType", "")
    c = toDict(getattr(d, "content", None))
    pExt = getattr(d, "paramsExt", None)
    p = getattr(pExt, "platformType", None) if pExt else None
    ms = mentionsData(d)

    if userId == "0" or uin == "0":
        s += 1

    params = c.get("params")
    if isinstance(params, str):
        if "styles" in params:
            s += 10
    elif isinstance(params, dict):
        if "styles" in params:
            s += 10

    if p == 1:
        s += 9
    elif p == 2:
        s += 7
    elif p == 0:
        return s

    if m in ("chat.photo", "chat.video.msg"):
        a = toDict(getattr(d, "attach", None))
        href = str(a.get("href", "")).lower()
        thumb = str(a.get("thumb", "")).lower()

        if thumb.startswith(("http://", "https://")) and any(x in thumb for x in ("t-", "b-")):
            s += 10

        if p in (1, 2):
            hosts = ("uguu", "catbox", "tmpfiles", "litter", "imgur", "github", "tiktok")
            if any(h in href or h in thumb for h in hosts):
                s += 10

        if ms:
            s += 10

    for me in ms:
        mid = str(getattr(me, "uid", "")) if hasattr(me, "uid") else str(toDict(me).get("uid", ""))
        if mid == uid:
            s += 10

    if m == "chat.reaction":
        rIcon = str(c.get("rIcon", ""))
        emojiPart, _ = react(rIcon)
        if emojiPart:
            s += 100

    if m == "chat.recommended":
        desc = toDict(c.get("description"))
        phone = str(desc.get("phone", "")).strip()
        if phone and not re.fullmatch(r"\d+", phone):
            s += 5

    return s

def antiBot(this, message, data, userId, threadId, type):
    if not hasattr(this, "_antiBotNotify"):
        this._antiBotNotify = {}

    if threadId not in ReadServices(this.uid).get("antiBot", []):
        return

    g = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
    if userId in g.get("adminIds", []) or userId == g.get("creatorId"):
        return
    if this.uid not in g.get("adminIds", []) and this.uid != g.get("creatorId"):
        return
    if skip(this, userId, threadId):
        return

    score = botLogic(this, data) or 0
    if score < 10:
        return

    key = (threadId, userId)
    now = time.time()
    last = this._antiBotNotify.get(key, 0)

    if now - last >= 300:
        this._antiBotNotify[key] = now
        p = getattr(getattr(data, "paramsExt", None), "platformType", None)
        this.sendMWarning(
            f"Client: {detectPlatform(p)}\nApi: {detectTypeSend(data)}",
            userId, threadId, type
        )

    this.blockUsers(userId, threadId)