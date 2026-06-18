from dto.index import *

def parseDuration(text):
    text = str(text or "").strip().lower()
    m = re.fullmatch(r"(\d+)\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours)", text)
    if not m:
        return None

    value = int(m.group(1))
    unit = m.group(2)

    if unit in {"s", "sec", "secs", "second", "seconds"}:
        return value
    if unit in {"m", "min", "mins", "minute", "minutes"}:
        return value * 60
    return value * 3600

def formatDuration(seconds):
    seconds = int(seconds or 0)
    if seconds <= 0:
        return "0s"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}min"
    return f"{seconds}s"

def parseReplyAndCooldown(text):
    text = str(text or "").strip()
    if not text:
        return "", 5

    parts = text.rsplit(" ", 1)
    if len(parts) < 2:
        return text, 5

    cooldown = parseDuration(parts[1])
    if cooldown is None:
        return text, 5

    reply = parts[0].strip()
    if not reply:
        return "", 5

    return reply, cooldown

def normalizeLearnEntry(entry):
    if isinstance(entry, dict):
        reply = str(entry.get("reply", "") or "").strip()
        cooldown = int(entry.get("cooldown", 5) or 5)
        return reply, max(0, cooldown)

    return str(entry or "").strip(), 5

def getLearnState(uid):
    s = ReadServices(uid) or {}
    learnStatus = dict(s.get("learnStatus") or {})
    learnStudent = bool(learnStatus.get("learnStudent", False))
    keywords = dict(learnStatus.get("keywords") or {})
    cooldowns = dict(learnStatus.get("cooldowns") or {})
    return s, learnStatus, learnStudent, keywords, cooldowns

def saveLearnState(uid, s, learnStatus, learnStudent, keywords, cooldowns):
    learnStatus["learnStudent"] = learnStudent
    learnStatus["keywords"] = keywords
    learnStatus["cooldowns"] = cooldowns
    s["learnStatus"] = learnStatus
    WriteService(uid, s)

def learnListen(this, message, data, userId, threadId, type):
    if data.uidFrom == 0:
        return
    
    text = str(getattr(data, "content", "") or "").strip().lower()
    if not text:
        return

    s, learnStatus, _, keywords, cooldowns = getLearnState(this.uid)
    if not bool(learnStatus.get("learnStudent", False)) or not keywords:
        return

    now = int(time.time())

    for key, entry in sorted(keywords.items(), key=lambda x: len(str(x[0])), reverse=True):
        key = str(key or "").strip().lower()
        if not key or key not in text:
            continue

        reply, cooldown = normalizeLearnEntry(entry)
        if not reply:
            return

        lastTime = int(cooldowns.get(key, 0) or 0)
        if cooldown > 0 and now - lastTime < cooldown:
            return

        cooldowns[key] = now
        saveLearnState(this.uid, s, learnStatus, True, keywords, cooldowns)

        this.sendMMessage(f"<textsize=18>{reply}<textsize=18>", None, threadId, type)
        return

def learnNow(this, message, data, userId, threadId, type):
    text = str(getattr(message, "text", "") or "").strip()
    parts = text.split()
    s, learnStatus, learnStudent, keywords, cooldowns = getLearnState(this.uid)

    if len(parts) < 2:
        learnStudent = not learnStudent
        saveLearnState(this.uid, s, learnStatus, learnStudent, keywords, cooldowns)

        this.sendMSuccess(
            f"Learn {'on' if learnStudent else 'off'}",
            userId,
            threadId,
            type
        )
        return

    action = parts[1].lower()

    if action == "add":
        body = text[len(parts[0]) + len(parts[1]) + 2:].strip()
        if "->" not in body:
            this.sendMFailed(
                "Syntax: learn add keyword -> reply 30s",
                userId,
                threadId,
                type
            )
            return

        key, value = map(str.strip, body.split("->", 1))
        reply, cooldown = parseReplyAndCooldown(value)

        if not key or not reply:
            this.sendMFailed(
                "Missing keyword or reply",
                userId,
                threadId,
                type
            )
            return

        key = key.lower()
        keywords[key] = {
            "reply": reply,
            "cooldown": cooldown
        }

        if key in cooldowns:
            del cooldowns[key]

        saveLearnState(this.uid, s, learnStatus, learnStudent, keywords, cooldowns)

        msg = f"Added: {key} with cooldown {formatDuration(cooldown)}"
        this.sendMSuccess(msg, userId, threadId, type)
        return

    if action == "rm":
        key = text[len(parts[0]) + len(parts[1]) + 2:].strip().lower()
        if not key:
            this.sendMFailed(
                "Syntax: learn rm keyword",
                userId,
                threadId,
                type
            )
            return

        if key not in keywords:
            this.sendMFailed(
                f"Keyword not found: {key}",
                userId,
                threadId,
                type
            )
            return

        del keywords[key]
        if key in cooldowns:
            del cooldowns[key]

        saveLearnState(this.uid, s, learnStatus, learnStudent, keywords, cooldowns)

        this.sendMSuccess(
            f"Removed: {key}",
            userId,
            threadId,
            type
        )
        return

    if action == "ls":
        if not keywords:
            this.sendMWarning("No learned keywords", userId, threadId, type)
            return

        lines = []
        for i, (key, entry) in enumerate(sorted(keywords.items()), 1):
            reply, cooldown = normalizeLearnEntry(entry)
            lines.append(f"{i}. {key} -> {reply} | {formatDuration(cooldown)}")

        this.sendMSuccess("\n".join(lines), userId, threadId, type)
        return

dependencies = {
    "name": "learn",
    "description": "Learn and reply",
    "permission": 3,
    "main": learnNow,
}