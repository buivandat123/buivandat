from functions.services.hook.bot_hook.mute_core import *

def silentCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    s = ReadServices(this.uid)

    silentRoot = s.setdefault("silent", {})
    groupMap = silentRoot.setdefault("group", {})
    silentMap = groupMap.setdefault(str(threadId), {})

    silentAllRoot = s.setdefault("isSlientAll", {})
    threadKey = str(threadId)
    isAll = bool(silentAllRoot.get(threadKey))

    now = time.time()
    for uid, meta in list(silentMap.items()):
        untilTs = (meta or {}).get("until", 0) or 0
        if untilTs and untilTs <= now:
            silentMap.pop(uid, None)

    uids = this.extractUids(data)
    if not uids and len(parts) >= 2 and parts[1].lower() not in ("list", "for"):
        return this.sendMWarning("Appoint a user to silent her/him..!", userId, threadId, type)
    sub = (parts[1] if len(parts) >= 2 else "").lower()

    if (len(parts) == 2 and not uids) or sub == "list":
        lines = [f"Silent All: {isAll}"]
        if not silentMap:
            lines.append("Silent list: Empty")
        else:
            items = sorted(silentMap.items(), key=lambda x: ((x[1] or {}).get("until", 0) or 0, x[0]))
            lines.append("Silent list:")
            lines.extend(
                f"{i}. {this.userName(uid)} | {formatRemaining((meta or {}).get('until', 0) or 0)} | by {this.userName((meta or {}).get('by')) if (meta or {}).get('by') else 'unknown'}"
                for i, (uid, meta) in enumerate(items, 1)
            )
        return this.sendMSuccess("\n".join(lines), userId, threadId, type)

    if len(parts) >= 3 and parts[1].lower() == "for" and parts[2] == "All":
        if len(parts) >= 4 and parts[3].lower() in ("on", "off"):
            enabled = parts[3].lower() == "on"
        else:
            enabled = not isAll

        if enabled:
            silentAllRoot[threadKey] = True
        else:
            silentAllRoot.pop(threadKey, None)

        WriteService(this.uid, s)
        return this.sendMSuccess(f"All {'members silented' if enabled else 'can talk now'}", -1, threadId, type)

    if not uids:
        return this.sendMWarning("Appoint a user to silent her/him..!", userId, threadId, type)

    action = "toggle" if sub in ("toggle", "add", "remove") else "toggle"

    durSeconds, durRaw = parseDuration(parts)
    if durSeconds is None:
        durSeconds, durRaw = 3600, "1h"

    changed = False
    for uid in uids:
        uidKey = str(uid)
        if uidKey in silentMap:
            silentMap.pop(uidKey, None)
            this.sendMSuccess(f"Unsilenced {this.userName(uid)}", userId, threadId, type)
            changed = True
            continue

        if durSeconds == 0:
            silentMap[uidKey] = {"until": 0, "by": userId, "at": now}
            this.sendMSuccess(f"Silenced {this.userName(uid)}", userId, threadId, type)
        else:
            silentMap[uidKey] = {"until": now + durSeconds, "by": userId, "at": now}
            this.sendMSuccess(f"Silenced {this.userName(uid)} {durRaw}", userId, threadId, type)
        changed = True

    if changed:
        WriteService(this.uid, s)

dependencies = {
    "name": "silent",
    "permission": 1,
    "cooldown": 3,
    "description": "Silent a user or for all",
    "main": silentCommand
}