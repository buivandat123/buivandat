from dto.index import *

def ParseKeyAsArgs(message):
    import shlex
    tokens = shlex.split((getattr(message, "text", None) or "").strip())
    args = {t.lower() for t in tokens[1:]}
    ignore = ""
    for i, t in enumerate(tokens):
        if t in ("-i", "--ignore") and i + 1 < len(tokens):
            ignore = tokens[i + 1] or ""
            break
    return args, ignore

def GetGroupInfo(this, threadId):
    gi = this.fetchGroupInfo(threadId)
    gridinfomap = getattr(gi, "gridInfoMap", None) or {}
    return gridinfomap.get(threadId, {}) or {}

def GetAdminIds(info):
    for k in ("adminIds", "adminIdList", "admins", "adminList", "adminIdMap", "adminMap", "adminUidList", "adminUidMap"):
        if k in info:
            v = info.get(k)
            if isinstance(v, dict):
                return [x for x in v.keys() if x]
            if isinstance(v, (list, tuple, set)):
                return [x for x in v if x]
            if isinstance(v, str):
                return [x for x in v.replace(" ", "").split(",") if x]
            return []
    return []

def GetUserName(this, uid):
    for fnname in ("userName", "getUserName", "getUserNick", "getUserNickname", "getDisplayName", "getUserDisplayName", "GetUserName"):
        fn = getattr(this, fnname, None)
        if callable(fn):
            try:
                n = fn(uid)
                if n:
                    return str(n)
            except:
                pass
    fn = getattr(this, "fetchUserInfo", None)
    if callable(fn):
        try:
            u = fn(uid)
            for k in ("name", "displayName", "fullName", "nickname"):
                n = getattr(u, k, None)
                if n:
                    return str(n)
        except:
            pass
    return ""

def keyAs(this, message, data, userId, threadId, type):
    args, ignore = ParseKeyAsArgs(message)
    isLeader = ":leader" in args
    isClear = ":clear" in args

    info = GetGroupInfo(this, threadId)
    creatorId = info.get("creatorId")
    creatorIdStr = str(creatorId) if creatorId is not None else ""

    if isClear:
        admins = GetAdminIds(info)
        if not admins:
            return this.sendMFailed("No admins to clear..!", userId, threadId, type)

        ignorekw = (ignore or "").casefold()
        targets = []
        seen = set()
        for uid in admins:
            if uid is None:
                continue
            uidstr = str(uid)
            if creatorIdStr and uidstr == creatorIdStr:
                continue
            if uidstr in seen:
                continue
            if ignorekw:
                name = GetUserName(this, uid).casefold()
                if ignorekw in name:
                    seen.add(uidstr)
                    continue
            seen.add(uidstr)
            targets.append(uid)

        if not targets:
            return this.sendMFailed("No valid targets..!", userId, threadId, type)

        tags = " ".join(f"@u{i}" for i in range(2, 2 + len(targets)))
        this.sendMSuccess(f"Cleared admins {tags}", [userId, *targets], threadId, type)
        this.removeAdmins(targets, threadId)
        return

    quote = getattr(data, "quote", None)
    uids = this.extractUids(data) or []

    targets = uids[:] if uids else []
    if not targets and quote:
        oid = getattr(quote, "ownerId", None)
        if oid:
            targets = [oid]
    if not targets:
        targets = [userId]

    seen = set()
    targets = [x for x in targets if x and (x not in seen and not seen.add(x))]

    if not targets:
        return this.sendMFailed("Can only key as members..!", userId, threadId, type)

    if isLeader:
        owners = []
        for uid in targets:
            if creatorIdStr and str(uid) == creatorIdStr:
                continue
            owners.append(uid)

        if not owners:
            return this.sendMFailed("No valid targets..!", userId, threadId, type)

        tags = " ".join(f"@u{i}" for i in range(2, 2 + len(owners)))
        this.sendMSuccess(f"Changed owner {tags}", [userId, *owners], threadId, type)
        for uid in owners:
            this.changeGroupOwner(uid, threadId)
        return

    promote = []
    demote = []
    for uid in targets:
        if creatorIdStr and str(uid) == creatorIdStr:
            continue
        (demote if isModerator(this, uid, threadId) else promote).append(uid)

    if not promote and not demote:
        return this.sendMFailed("No valid targets..!", userId, threadId, type)

    allTargets = promote + demote
    tags = " ".join(f"@u{i}" for i in range(2, 2 + len(allTargets)))

    msgParts = []
    if promote:
        msgParts.append("Promoted")
    if demote:
        msgParts.append("Demoted")
    this.sendMSuccess(f"{' & '.join(msgParts)} {tags}", [userId, *allTargets], threadId, type)

    if promote:
        this.addAdmins(promote, threadId)
    if demote:
        this.removeAdmins(demote, threadId)

dependencies = {
    "name": "key-as",
    "permission": 4,
    "description": "Give key to a member",
    "cooldown": 5,
    "main": keyAs
}