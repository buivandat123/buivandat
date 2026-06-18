from functions.services.hook.core_hook.extra_multibot_core import *

def _MentionsToUids(data):
    ms = getattr(data, "mentions", None) or []
    out = []
    for m in ms:
        try:
            uid = m.get("uid") if isinstance(m, dict) else getattr(m, "uid", None)
        except:
            uid = None
        uid = str(uid or "").strip()
        if uid:
            out.append(uid)
    return list(dict.fromkeys(out))

def _ReadList(path):
    try:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            v = json.loads(f.read() or "[]")
        return v if isinstance(v, list) else []
    except:
        return []

def _WriteList(path, items):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=4))

def _ResolveLoginFile(this, oldUid, indexToken):
    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {})
    if not isinstance(dataBot, dict):
        dataBot = {}

    if indexToken and str(indexToken).isdigit():
        i = int(indexToken)
        if i < 1 or i > 100:
            return None, None, None
        loginFile = f"{i}-login.json"
        loginPath = os.path.join("assets", "config", "multibot", loginFile)
        if not os.path.exists(loginPath):
            return None, None, None
        return loginFile, dataConfig, dataBot

    loginFile = str(dataBot.get(str(oldUid)) or "").strip()
    if not loginFile:
        return None, None, None
    return loginFile, dataConfig, dataBot

def ChangeOwnerBot(this, message, data, userId, threadId, type):
    uidFrom = GetUidFrom(data)
    if not uidFrom:
        return SendMention(this, "status:null", userId, threadId, type)

    raw = (message.text or "").strip()
    parts = raw.split()
    if len(parts) < 2:
        return SendMention(this, "What do u wanna do?", userId, threadId, type)

    token = parts[1] if len(parts) > 1 else None
    uids = _MentionsToUids(data)

    oldUid = None
    newUid = None

    if token and str(token).isdigit():
        if len(uids) < 1:
            return SendMention(this, "Mention new owner", userId, threadId, type)
        newUid = uids[0]
    else:
        if len(uids) < 2:
            return SendMention(this, "Mention old and new owner", userId, threadId, type)
        oldUid, newUid = uids[0], uids[1]

    loginFile, dataConfig, dataBot = _ResolveLoginFile(this, oldUid, token if (token and str(token).isdigit()) else None)
    if not loginFile:
        return SendMention(this, "Cannot resolve bot login file", userId, threadId, type)

    loginPath = os.path.join("assets", "config", "multibot", loginFile)
    items = _ReadList(loginPath)

    if token and str(token).isdigit():
        oldUid = None
        for it in items:
            if isinstance(it, dict) and it.get("userClientId"):
                oldUid = str(it.get("userClientId")).strip()
                if oldUid:
                    break
        if not oldUid:
            return SendMention(this, "Cannot resolve old owner in login file", userId, threadId, type)

    oldUid = str(oldUid or "").strip()
    newUid = str(newUid or "").strip()
    if not oldUid or not newUid:
        return SendMention(this, "Invalid uid", userId, threadId, type)
    if oldUid == newUid:
        return SendMention(this, "Old/New uid is same", userId, threadId, type)

    changed = False
    for it in items:
        if not isinstance(it, dict):
            continue
        if str(it.get("userClientId") or "").strip() == oldUid:
            it["userClientId"] = newUid
            changed = True
        if str(it.get("clientBotId") or "").strip() == oldUid:
            it["clientBotId"] = newUid
            changed = True

    if changed:
        _WriteList(loginPath, items)

    dataBot = dataConfig.get("dataBot", {})
    if not isinstance(dataBot, dict):
        dataBot = {}
    dataBot.pop(oldUid, None)
    dataBot[newUid] = loginFile
    dataConfig["dataBot"] = dataBot
    saveJson(mainLogin, dataConfig)

    return SendMention(this, f"Changed owner {oldUid} -> {newUid} | {loginFile}", userId, threadId, type)