from functions.services.hook.anti_hook.shield_hook import *

def VerifyCommand(this, message, data, userId, threadId, type):
    try:
        parts = (message.text or "").strip().split()
        s = ReadServices(this.uid)

        verifyOn = s.setdefault("verifyOn", [])
        tid = str(threadId)
        enabled = tid in verifyOn

        if len(parts) >= 2 and parts[1] == "--flag":
            uids = this.extractUids(data)
            if not uids:
                return this.sendMWarning(f"Use: {this.prefix}{this.rawCommand} --flag @User", userId, threadId, type)

            v = s.get(VerifyKey)
            if not isinstance(v, dict):
                v = {}
                s[VerifyKey] = v
            g = v.get(tid)
            if not isinstance(g, dict):
                g = {}
                v[tid] = g

            silentMap = s.setdefault("silent", {}).setdefault("group", {}).setdefault(tid, {})
            now = time.time()
            n = 0

            for uid in uids:
                uid = str(uid)
                if uid == str(this.uid):
                    continue
                p = g.get(uid)
                if isinstance(p, dict) and int(p.get("ok") or 0):
                    continue

                token = "".join(random.choice("0123456789") for _ in range(8)) + "-" + "".join(random.choice("0123456789") for _ in range(6)) + "-?verifyCaptcha"
                g[uid] = {"t": token, "ts": now, "try": 0, "ok": 0}
                silentMap[uid] = {"until": 0, "by": str(userId), "at": now}
                n += 1

                txt = f"You got flag to verify Client, send correctly this code to verify:\n{token}"
                try:
                    this.sendMWarning(txt, uid, tid, type)
                except:
                    pass

            v[tid] = g
            s[VerifyKey] = v
            WriteService(this.uid, s)
            return
        
        if len(parts) >= 2 and parts[1] == "--unflag":
            uids = this.extractUids(data)
            if not uids:
                return this.sendMWarning(
                    f"Use: {this.prefix}{this.rawCommand} --unflag @User",
                    userId, threadId, type
                )

            v = s.get(VerifyKey)
            if not isinstance(v, dict):
                return

            g = v.get(tid)
            if not isinstance(g, dict):
                return

            silentGroup = s.get("silent", {}).get("group", {}).get(tid, {})
            n = 0

            for uid in uids:
                uid = str(uid)
                if uid == str(this.uid):
                    continue

                if uid in g:
                    g.pop(uid, None)
                    silentGroup.pop(uid, None)
                    n += 1

            if not g:
                v.pop(tid, None)

            WriteService(this.uid, s)

            if n:
                this.sendMWarning(
                    f"Removed verify flag for {n} user(s).",
                    userId, threadId, type
                )
            return


        if len(parts) < 2:
            enabled = not enabled
        elif parts[1].lower() == "on":
            enabled = True
        elif parts[1].lower() == "off":
            enabled = False
        else:
            return

        if enabled and tid not in verifyOn:
            verifyOn.append(tid)
        if not enabled and tid in verifyOn:
            verifyOn.remove(tid)

        WriteService(this.uid, s)
        this.sendMSuccess(f"Verify is now {'enabled' if enabled else 'disabled'} in this {this.groupHub(threadId)}, Anyone joined this group must verify.", userId, threadId, type)
    except:
        pass

dependencies = {
    "name": "verify",
    "permission": 3,
    "description": "Verify Shield Captcha",
    "cooldown": 3,
    "main": VerifyCommand
}