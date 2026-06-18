from dto.index import *

def BlockCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    args = {p.lower() for p in parts[1:]}
    targetAll = any(p.lower() == ":target-all" for p in parts[1:])

    def Message(T, S=False, F=False, W=False):
        if S: return this.sendMSuccess(T, userId, threadId, type)
        if F: return this.sendMFailed(T, userId, threadId, type)
        if W: return this.sendMWarning(T, userId, threadId, type)
        return this.sendMMessage(T, userId, threadId, type)

    def LoadBl(TID):
        s = ReadServices(this.uid)
        return s, s.setdefault("blacklist", {}).setdefault(TID, [])

    def Kick(UID, TID):
        fn = getattr(this, "kickUsers", None) or getattr(this, "kickUser", None) or getattr(this, "removeGroupMembers", None)
        if not fn:
            return False
        try:
            if fn.__name__ == "kickUser":
                fn(UID, TID)
            else:
                fn([UID], TID)
            return True
        except:
            return False

    if "-ls" in args:
        _, bl = LoadBl(threadId)
        if not bl:
            return Message("Don't have any enemy..!", W=True)
        return this.sendMCustom(
            "ENEMY TARGET", "r",
            "\n" + "\n".join(f"{i}. {this.userName(uid)}" for i, uid in enumerate(bl, 1)),
            userId, threadId, type
        )

    if "-rm" in args:
        rmArg = next((parts[i + 1] for i in range(len(parts) - 1) if parts[i].lower() == "-rm"), None)
        if not rmArg:
            return Message("Type a index or enemyId to remove from target", W=True)

        s, bl = LoadBl(threadId)

        if rmArg.isdigit():
            idx = int(rmArg) - 1
            if not (0 <= idx < len(bl)):
                return Message("Invalid index?", F=True)
            uidRemoved = bl.pop(idx)
        else:
            if rmArg not in bl:
                return Message("Not found..!", F=True)
            bl.remove(rmArg)
            uidRemoved = rmArg

        WriteService(this.uid, s)
        return Message(f"Removed enemy {this.userName(uidRemoved)} from target list!!!", S=True)

    quote = getattr(data, "quote", None)
    targets = this.extractUids(data) or ([getattr(quote, "ownerId", None)] if quote else [])
    seen = set()
    targets = [x for x in targets if x and (x not in seen and not seen.add(x))]

    if not targets:
        cmd = this.prefix + this.rawCommand
        Help = (f"""Quote or mentions a target to block:
    Args:
    {cmd} -odds: Target, Can't join group again
    {cmd} -rm: Remove target
    {cmd} -ls: Get target list
    Spec:
    {cmd} -odds :target-all: Target a enemy for all groups""")
        return Message(Help, W=True)

    tags = " ".join(f"@u{i}" for i in range(2, 2 + len(targets)))
    this.sendMMessage(f"Blocked {tags} out", [userId, *targets], threadId, type)
    this.blockUsers(targets, threadId)

    if "-odds" in args:
        s, bl = LoadBl(threadId)
        changed = False
        for uid in targets:
            if uid not in bl:
                bl.append(uid)
                changed = True
        if changed:
            WriteService(this.uid, s)

        if targetAll:
            g = this.fetchAllGroups()
            grids = list(getattr(g, "gridVerMap", {}) or {})
            kicked = 0
            checked = 0

            for gid in grids:
                mem = this.getGroupMember(gid)
                profiles = getattr(mem, "profiles", {}) or {}
                checked += 1
                for uid in targets:
                    if uid in profiles and Kick(uid, gid):
                        kicked += 1

            return
def blacklistEvent(this):
    def loop():
        while True:
            s = ReadServices(this.uid)
            bls = s.get("blacklist", {})
            for threadId, uids in bls.items():
                for uid in uids:
                    this.blockUsers(uid, threadId)
            time.sleep(1)

    t = threading.Thread(target=loop, daemon=True)
    t.start()

dependencies = {
    "name": "block",
    "permission": 2,
    "description": "Block out a member",
    "cooldown": 5,
    "main": BlockCommand
}