from functions.services.hook.anti_hook.filter_hook import *

def FilterCommand(this, message, data, userId, threadId, type):
    try:
        parts = (message.text or "").strip().split()
        if len(parts) < 2:
            return this.sendMWarning(f"Use {this.prefix}{this.rawCommand} to filter any special u wanna ban", userId, threadId, type)

        action = parts[1].lower()
        s = ReadServices(this.uid)

        if action == "badword":
            store = s.setdefault("filterBadword", {})
            words = store.setdefault(str(threadId), [])

            if len(parts) < 3:
                if not words:
                    return this.sendMWarning("Badword list is empty.", userId, threadId, type)
                return this.sendMSuccess("Badword list:\n" + "\n".join(f"{i}. {w}" for i, w in enumerate(words, 1)), userId, threadId, type)

            w = " ".join(parts[2:]).strip()
            wn = re.sub(r"\s+", " ", w.lower()).strip()
            if not wn: return

            cur = {re.sub(r"\s+", " ", str(x).lower()).strip(): x for x in words}
            if wn in cur:
                old = cur[wn]
                store[str(threadId)] = [x for x in words if re.sub(r"\s+", " ", str(x).lower()).strip() != wn]
                WriteService(this.uid, s)
                return this.sendMSuccess(f"Removed badword: {old}", userId, threadId, type)

            words.append(w)
            store[str(threadId)] = words
            WriteService(this.uid, s)
            return this.sendMSuccess(f"Added badword: {w}", userId, threadId, type)

        if action == "nsfw":
            store = s.setdefault("filterNsfw", {})
            cfg = store.setdefault(str(threadId), {"enabled": False, "threshold": 0.8})
            if not isinstance(cfg, dict):
                cfg = {"enabled": False, "threshold": 0.8}
                store[str(threadId)] = cfg

            if len(parts) == 2:
                cfg["enabled"] = not bool(cfg.get("enabled", False))
                WriteService(this.uid, s)
                try: th = float(cfg.get("threshold", 0.8))
                except: th = 0.8
                if th > 1: th /= 100.0
                state = "enabled" if cfg["enabled"] else "disabled"
                return this.sendMSuccess(f"{state} filter nsfw media", userId, threadId, type)

            sub = parts[2].lower()
            val = sub[:-1].strip() if sub.endswith("%") else sub
            try:
                th = float(val)
            except:
                return this.sendMWarning(f"{this.prefix}{this.rawCommand} nsfw or set {this.prefix}{this.rawCommand} nsfw 80%", userId, threadId, type)

            if th > 1: th /= 100.0
            if th <= 0: th = 0.05
            if th > 1: th = 1.0

            cfg["enabled"] = True
            cfg["threshold"] = th
            WriteService(this.uid, s)
            return

    except:
        try: this.replyMessage(Message(text="Error"), data, threadId, type)
        except: pass

dependencies = {
    "name": "filter",
    "permission": 3,
    "description": "Filter messages,..",
    "cooldown": 3,
    "main": FilterCommand
}