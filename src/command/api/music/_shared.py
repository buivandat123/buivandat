from dto.index import *
from functions.engine.data.data import ReadServices, WriteService
from functions.engine.data.mediaEngine import MediaCache


def FmtDuration(t):
    try:
        t = int(t or 0)
    except:
        t = 0
    if t > 24 * 3600:
        t //= 1000
    h, t = divmod(t, 3600)
    m, s = divmod(t, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def EnsureMediaCache(this):
    if hasattr(this, "MediaCache") and getattr(this, "MediaCache", None):
        return
    try:
        this.MediaCache = MediaCache(owner=this)
        return
    except:
        try:
            this.MediaCache = MediaCache()
        except:
            this.MediaCache = None


def CacheGet(cache, k, d=None):
    if not isinstance(cache, dict):
        return d
    v = cache.get(k)
    if v is not None:
        return v
    meta = cache.get("meta")
    if isinstance(meta, dict):
        v2 = meta.get(k)
        if v2 is not None:
            return v2
    return d


def IsAlive(this, url):
    try:
        return bool(url) and getattr(this, "MediaCache", None) and this.MediaCache.isAlive(url)
    except:
        return False


def ParseCommandArgs(this, text, defaultCmd):
    s = str(text or "").strip()
    p = str(getattr(this, "prefix", "") or "")
    if p and s.startswith(p):
        s = s[len(p):].lstrip()

    cmd = str(getattr(this, "commandName", "") or getattr(this, "rawCommand", "") or defaultCmd).strip().lower()
    if cmd and s.lower().startswith(cmd):
        s = s[len(cmd):].lstrip()
    if cmd and s.lower().startswith(cmd):
        s = s[len(cmd):].lstrip()
    return s


def StripSelectionText(message, data):
    if isinstance(message, Message):
        text = message.text or ""
    else:
        text = str(message or "")
    text = text.strip()
    mentions = data.get("mentions") or []
    mentions = sorted(mentions, key=lambda x: x.get("pos", 0), reverse=True)
    for m in mentions:
        pos = m.get("pos", 0)
        ln = m.get("len", 0)
        if pos >= 0 and ln > 0:
            text = text[:pos] + text[pos + ln:]
    text = "".join(c for c in text if c.isdigit() or c.isspace()).strip()
    return text


def ToggleSpinDisk(this, threadId, userId, type, serviceKey, enabled):
    s = ReadServices(this.uid)
    a = s.setdefault(serviceKey, [])
    e = threadId in a
    if enabled is None:
        e = not e
    else:
        e = bool(enabled)
    if e and threadId not in a:
        a.append(threadId)
    if not e and threadId in a:
        a.remove(threadId)
    WriteService(this.uid, s)
    this.sendMSuccess(
        f"SpinDisk is now {'enabled, if you search songs and choose, it will have a disk' if e else 'disabled'}.",
        userId,
        threadId,
        type,
    )


def StartSelectionCooldown(this, cooldownAttr, msg, threadId, type, timeout=120):
    if not msg:
        return
    if not hasattr(this, cooldownAttr):
        setattr(this, cooldownAttr, {})
    cooldown = getattr(this, cooldownAttr)
    k = getattr(msg, "msgId", None)
    if not k:
        return
    cooldown[k] = True
    msgObj = MessageObject(msgId=msg.msgId, cliMsgId=msg.clientId, msgType="chat.photo")

    def Loop():
        for i in range(int(timeout), 0, -1):
            if not cooldown.get(k):
                break
            this.sendMultiReaction(msgObj, "🕑", threadId, type, 102229, numreact=i)
            time.sleep(1)
            this.sendMultiReaction(msgObj, "", threadId, type, -1, numreact=i)
        cooldown.pop(k, None)

    threading.Thread(target=Loop, daemon=True).start()


def InitSelectionTimeout(this, stateAttr, interval=1, timeout=120):
    if not hasattr(this, stateAttr):
        setattr(this, stateAttr, {})

    def Loop():
        while True:
            now = time.time()
            states = getattr(this, stateAttr, {})
            for uid, st in list(states.items()):
                if now - (st.get("time") or 0) > timeout:
                    states.pop(uid, None)
                    try:
                        this.deleteMessage(st["msgId"], this.uid, st["cliMsgId"], st["threadId"])
                    except:
                        pass
                    this.sendMCustom("Timeout", "y", "Please search again", uid, st["threadId"], st["typeGr"])
            time.sleep(interval)

    threading.Thread(target=Loop, daemon=True).start()
