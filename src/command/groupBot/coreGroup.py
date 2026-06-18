from dto.index import *
import re, json, time, unicodedata, shlex

def Norm(s):
    return (s or "").strip()

def NormUnicode(s):
    s = unicodedata.normalize("NFKC", str(s or ""))
    out = []
    for ch in s:
        try:
            name = unicodedata.name(ch)
        except ValueError:
            out.append(ch)
            continue

        if "SQUARED LATIN CAPITAL LETTER" in name or "NEGATIVE SQUARED LATIN CAPITAL LETTER" in name:
            out.append(name.split("LETTER ")[-1])
            continue

        if "LATIN LETTER SMALL CAPITAL" in name:
            out.append(name.split("CAPITAL ")[-1].lower())
            continue

        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out)).strip()

def GetQuoteLink(data):
    q = getattr(data, "quote", None)
    if not q:
        return None

    msg = Norm(getattr(q, "msg", ""))
    if msg:
        m = re.search(r"https?://zalo\.me/g/\S+", msg)
        if m:
            return m.group(0)

    attach = getattr(q, "attach", None)
    if not attach:
        return None

    if isinstance(attach, str):
        attach = json.loads(attach)
    return (attach or {}).get("href")

def ParseLeaveArgs(message):
    tokens = shlex.split(Norm(getattr(message, "text", "")))
    args = {t.lower() for t in tokens[1:]}
    search = []
    ignore = []

    i = 1
    while i < len(tokens):
        t = tokens[i]
        tl = t.lower()

        if tl in ("-s", "--search"):
            raw = " ".join(tokens[i + 1:]).strip()
            if raw:
                quoted = re.findall(r'"([^"]+)"', raw)
                if quoted:
                    search = [x.strip() for x in quoted if x.strip()]
                else:
                    raw = raw.replace(",", " ")
                    search = [x.strip() for x in raw.split() if x.strip()]
            i = len(tokens)
            continue

        if tl in ("-i", "--ignore"):
            i += 1
            while i < len(tokens):
                x = tokens[i]
                xl = x.lower()
                if xl in ("-s", "--search", "-i", "--ignore", "all", ":settings-lockchat"):
                    break
                ignore.append(x)
                i += 1
            continue

        i += 1

    return args, search, ignore

def groupNameMap(this, threadIds):
    ids = [str(x) for x in threadIds]
    return {gid: this.fetchGroupInfo(gid).gridInfoMap[gid]["name"] for gid in ids}

def joinGroupCommand(this, message, data, userId, threadId, type):
    if ":auto" in data.content:
        s = ReadServices(this.uid) or {}
        cur = bool(s.get("autoJoinGroups", False))
        new = not cur
        s["autoJoinGroups"] = new
        WriteService(this.uid, s)
        mes = f"Auto join groups has been {'on' if new else 'off'}"
        this.sendMSuccess(mes, userId, threadId, type)
        return

    text = Norm(getattr(message, "text", ""))
    parts = text.split()
    link = parts[1] if len(parts) > 1 else GetQuoteLink(data)

    link = Norm(link)
    if not link:
        return this.sendMWarning("Give me group link or quote a message containing it.", userId, threadId, type)

    m = re.match(r"^https?://zalo\.me/g/([^\s/?#]+)", link)
    if not m:
        return this.sendMFailed("Invalid group link.", userId, threadId, type)

    link = f"https://zalo.me/g/{m.group(1)}"
    code = this.joinGroup(link)
    if isinstance(code, dict):
        code = code.get("errorCode", code.get("error_code", code.get("code", code.get("status", code.get("error", 0)))))
    try:
        code = int(code)
    except Exception:
        code = -1

    msg = {
        0: f"Joined {link}",
        240: "I've sent join request, waiting for approval",
        257: "I got limited requests..!",
        178: "I has been joined this group before",
        227: "No data..",
        175: "I got blocked from that..",
        1003: "Group has been full",
        1004: "Group has been full",
        1022: "I've sent join request, waiting for approval",
    }.get(code, f"Join failed ({code})")

    return this.sendMSuccess(msg, userId, threadId, type)

def autoJoinGroups(this, message, data, userId, threadId, type):
    setting = ReadServices(this.uid) or {}
    if not setting.get("autoJoinGroups", False):
        return

    link = message if isinstance(message, str) else (getattr(message, "text", "") or "")
    if data.msgType == "chat.recommended":
        link = data.content.get("href")

    match = re.search(r"https?://zalo\.me/g/([^\s/?#]+)", link)
    if not match:
        return

    link = f"https://zalo.me/g/{match.group(1)}"
    code = this.joinGroup(link)
    if isinstance(code, dict):
        code = code.get("errorCode", code.get("error_code", code.get("code", code.get("status", code.get("error", 0)))))
    try:
        code = int(code)
    except Exception:
        code = -1

    msg = {
        0: f"Joined {link}",
        240: "I've sent join request, waiting for approval",
        257: "I got limited requests..!",
        178: "I has been joined this group before",
        227: "No data..",
        175: "I got blocked from that..",
        1003: "Group has been full",
        1004: "Group has been full",
        1022: "I've sent join request, waiting for approval",
    }.get(code, f"Join failed ({code})")
    this.sendMSuccess(msg, userId, threadId, type)

def leaveGroup(this, message, data, userId, threadId, type):
    args, search, ignore = ParseLeaveArgs(message)

    searchkws = [NormUnicode(x).casefold() for x in (search or []) if str(x or "").strip()]
    ignorekws = [NormUnicode(x).casefold() for x in (ignore or []) if str(x or "").strip()]

    hasSearch = "-s" in args or "--search" in args
    hasIgnore = "-i" in args or "--ignore" in args
    hasLock = ":s-lockchat" in args
    hasAll = "all" in args

    if hasAll or hasLock or hasSearch or hasIgnore:
        if hasSearch and not searchkws and not hasAll:
            return this.sendMFailed('Missing keyword: leave -s "từ khóa"', userId, threadId, type)

        gids = [str(g) for g in this.fetchAllGroups().gridVerMap.keys()]
        names = groupNameMap(this, gids)

        left = []
        failed = []

        for gid in gids:
            name = names.get(gid, "") or ""
            namecf = NormUnicode(name).casefold()

            if hasIgnore and ignorekws and any(k in namecf for k in ignorekws):
                continue
            if hasSearch and searchkws and not any(k in namecf for k in searchkws):
                continue
            if hasLock:
                info = this.fetchGroupInfo(gid).gridInfoMap[gid]
                if ((info.get("setting") or {}).get("lockSendMsg") != 1):
                    continue

            ok = this.leaveGroup(gid)
            (failed if ok is False else left).append(gid)

        lines = [f"Left: {len(left)}"]
        if left:
            lines += [f"- {names.get(g, '')}" for g in left[:60]]
            if len(left) > 60:
                lines.append(f"... +{len(left) - 60} more")

        if failed:
            lines.append(f"Failed: {len(failed)}")
            lines += [f"- {g} | {names.get(g, '')}" for g in failed[:30]]
            if len(failed) > 30:
                lines.append(f"... +{len(failed) - 30} more")
            return this.sendMFailed("\n".join(lines), userId, threadId, type)

        return this.sendMSuccess("\n".join(lines), userId, threadId, type)

    this.sendMSuccess("Goodbye..!", userId, threadId, type)
    this.leaveGroup(threadId)
    return

dependencies = {
    "name": ["join", "leave"],
    "permission": 4,
    "description": ["Join group", "Leave group"],
    "cooldown": 5,
    "main": [joinGroupCommand, leaveGroup]
}