from dto.index import *

def WhitelistCommand(this, message, data, userId, threadId, type):
    try:
        parts = (message.text or "").strip().split()
        s = ReadServices(this.uid)
        wl = s.setdefault("whitelist", {}).setdefault(threadId, [])
        uids = this.extractUids(data) or []
        quote = getattr(data, "quote", None)

        arg = parts[1].lower() if len(parts) > 1 else ""

        if arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(wl):
                uid = wl.pop(idx)
                WriteService(this.uid, s)
                return this.sendMSuccess(f"Removed whitelist {this.userName(uid)}", userId, threadId, type)
            return this.sendMFailed("Invalid index", userId, threadId, type)

        targets = uids[:] if uids else []
        if not targets and quote:
            oid = getattr(quote, "ownerId", None)
            if oid:
                targets = [oid]

        if not targets:
            if len(parts) < 2:
                if not wl:
                    return this.sendMSuccess("Whitelist empty", userId, threadId, type)
                msg = "Whitelist:\n" + "\n".join(f"{i}. {this.userName(uid)}" for i, uid in enumerate(wl, 1))
                return this.sendMSuccess(msg, userId, threadId, type)

            return this.sendMWarning("Assign any users to whitelist..!", userId, threadId, type)

        added = 0
        for uid in targets:
            if uid not in wl:
                wl.append(uid)
                added += 1

        if added:
            WriteService(this.uid, s)

        if len(targets) == 1:
            return this.sendMSuccess(f"Whitelisted {this.userName(targets[0])}", userId, threadId, type)

        tags = " ".join(f"@u{i}" for i in range(2, 2 + len(targets)))
        return this.sendMSuccess(f"Whitelisted {tags}", [userId, *targets], threadId, type)
    except:
        return this.sendMFailed("Error", userId, threadId, type)

dependencies = {
    "name": "whitelist",
    "permission": 3,
    "description": "Whitelist manager",
    "cooldown": 5,
    "main": WhitelistCommand
}