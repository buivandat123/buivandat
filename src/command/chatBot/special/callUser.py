from dto.index import *

def _GetCallTime(message, data):
    t = (getattr(message, "text", "") or "").strip()
    if isinstance(data, dict):
        t2 = (data.get("content") or "").strip()
        if t2 and (not t or len(t2) > len(t)):
            t = t2

    parts = t.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        return int(parts[-1])

    m = re.search(r"(\d+)\s*$", t)
    if m:
        return int(m.group(1))

    return 1

def CallUser(this, message, data, userId, threadId, type):
    mentions = this.extractUids(data) or []
    if not mentions:
        this.sendMWarning("No target", userId, threadId, type)
        return

    callTime = _GetCallTime(message, data)
    if callTime < 1 or callTime > 500:
        this.sendMWarning("Invalid call time", userId, threadId, type)
        return

    for uid in mentions:
        for _ in range(callTime):
            this.sendCall(uid, this.randomInt())
            time.sleep(1.5)

    this.sendMSuccess(f"Call {callTime} times to {len(mentions)} targets", userId, threadId, type)

dependencies = {
    "name": "call",
    "permission": 3,
    "description": "Call user",
    "cooldown": 5,
    "main": CallUser
}