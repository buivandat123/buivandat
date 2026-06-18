from dto.index import *

VerifyKey = "verifyShield"
VerifyTimeout = 180
VerifyMaxTry = 5
VerifyShareWindow = 10

def IsVerify(this, eventData, eventType):
    try:
        if eventType != GroupEventType.JOIN:
            return False

        tid = str(eventData.groupId)
        s = ReadServices(this.uid)
        if tid not in (s.get("verifyOn", []) or []):
            return False

        v = s.get(VerifyKey)
        if not isinstance(v, dict):
            v = {}
            s[VerifyKey] = v
        g = v.get(tid)
        if not isinstance(g, dict):
            g = {}
            v[tid] = g

        members = list(eventData.updateMembers or [])
        if not members:
            return False

        now = time.time()
        silentMap = s.setdefault("silent", {}).setdefault("group", {}).setdefault(tid, {})
        multi = len(members) >= 2

        token = ""
        if multi:
            session = g.get("@session")
            if not isinstance(session, dict) or (now - float(session.get("ts") or 0)) > VerifyShareWindow:
                token = "".join(random.choice("0123456789") for _ in range(8)) + "-" + "".join(random.choice("0123456789") for _ in range(6)) + "-?verifyCaptcha"
                session = {"t": token, "ts": now, "sent": 0}
                g["@session"] = session
            token = str(g.get("@session", {}).get("t") or "")
        else:
            g.pop("@session", None)

        joined = []
        for m in members:
            uid = str(m.get("id") or "")
            if not uid or uid == str(this.uid):
                continue

            p = g.get(uid)
            if isinstance(p, dict) and int(p.get("ok") or 0):
                continue

            if multi:
                token = token
            else:
                token = "".join(random.choice("0123456789") for _ in range(8)) + "-" + "".join(random.choice("0123456789") for _ in range(6)) + "-?verifyCaptcha"

            g[uid] = {"t": token, "ts": now, "try": 0, "ok": 0}
            silentMap[uid] = {"until": 0, "by": str(this.uid), "at": now}
            joined.append(uid)

        v[tid] = g
        s[VerifyKey] = v
        WriteService(this.uid, s)

        if not joined:
            return True

        if multi:
            session = g.get("@session") or {}
            if (now - float(session.get("sent") or 0)) > VerifyShareWindow:
                session["sent"] = now
                g["@session"] = session
                v[tid] = g
                s[VerifyKey] = v
                WriteService(this.uid, s)

                msg = f"Please send correctly this code to verify:\n{token}"
                try:
                    this.sendMessage(msg, tid, ThreadType.GROUP)
                except:
                    pass

            msgDm = f"Please send correctly this code to verify:\n{token}"
            for uid in joined:
                try:
                    this.sendMWarning(msgDm, uid, uid, ThreadType.USER)
                except:
                    pass
        else:
            uid = joined[0]
            token = str(g.get(uid, {}).get("t") or "")
            msg = f"Please send correctly this code to verify:\n{token}"
            try:
                this.sendMWarning(msg, uid, tid, ThreadType.GROUP)
                this.sendMWarning(msg, uid, uid, ThreadType.USER)
            except:
                try:
                    this.sendMessage(msg, tid, ThreadType.GROUP)
                except:
                    pass

        return True
    except:
        return False
def VerifyShieldCaptcha(this, message, data, userId, threadId, type):
    try:
        if getattr(data, "msgType", None) == "chat.reaction":
            return

        tid = str(threadId)
        fromId = str(getattr(data, "uidFrom", None) or userId)

        s = ReadServices(this.uid)
        if tid not in (s.get("verifyOn", []) or []):
            return

        v = s.get(VerifyKey)
        if not isinstance(v, dict):
            return
        g = v.get(tid)
        if not isinstance(g, dict):
            return
        p = g.get(fromId)
        if not isinstance(p, dict) or int(p.get("ok") or 0):
            return

        silentMap = s.setdefault("silent", {}).setdefault("group", {}).setdefault(tid, {})

        now = time.time()
        ts = float(p.get("ts") or 0)

        raw = message
        if raw is None:
            raw = str(message or "")
        raw = raw.strip()

        token = str(p.get("t") or "").strip()
        m = re.search(r"\d{8}-\d{6}-\?verifyCaptcha", raw)
        txt = m.group(0) if m else raw

        if ts and (now - ts) > VerifyTimeout:
            if len([k for k in g.keys() if k not in ["@session"] and isinstance(g.get(k), dict) and not int(g.get(k).get("ok") or 0)]) >= 2:
                session = g.get("@session")
                if not isinstance(session, dict) or (now - float(session.get("ts") or 0)) > VerifyShareWindow:
                    token2 = "".join(random.choice("0123456789") for _ in range(8)) + "-" + "".join(random.choice("0123456789") for _ in range(6)) + "-?verifyCaptcha"
                    session = {"t": token2, "ts": now, "sent": 0}
                    g["@session"] = session
                token2 = str(g.get("@session", {}).get("t") or token)
            else:
                token2 = "".join(random.choice("0123456789") for _ in range(8)) + "-" + "".join(random.choice("0123456789") for _ in range(6)) + "-?verifyCaptcha"

            p["t"] = token2
            p["ts"] = now
            p["try"] = int(p.get("try") or 0)
            p["ok"] = 0
            g[fromId] = p
            v[tid] = g
            s[VerifyKey] = v

            silentMap[fromId] = {"until": 0, "by": str(this.uid), "at": now}
            WriteService(this.uid, s)

            msg = f"Please send correctly this code to verify:\n{token2}"
            try:
                this.sendMWarning(msg, fromId, fromId, ThreadType.USER)
            except:
                pass
            try:
                this.deleteMessage(data.msgId, getattr(data, "uidFrom", this.uid), data.cliMsgId, tid)
            except:
                pass
            return

        if token and (token in txt or txt == token):
            silentMap.pop(fromId, None)

            g.pop(fromId, None)

            alive = False
            for k, pv in g.items():
                if k == "@session":
                    continue
                if isinstance(pv, dict) and not int(pv.get("ok") or 0):
                    alive = True
                    break

            if not alive:
                g.pop("@session", None)
                v.pop(tid, None)
            else:
                v[tid] = g

            s[VerifyKey] = v
            WriteService(this.uid, s)

            try:
                this.sendMSuccess("Verify successful, you can connect..", fromId, tid, type)
            except:
                pass
            try:
                this.deleteMessage(data.msgId, getattr(data, "uidFrom", this.uid), data.cliMsgId, tid)
            except:
                pass
            return

        p["try"] = int(p.get("try") or 0) + 1
        g[fromId] = p
        v[tid] = g
        s[VerifyKey] = v
        WriteService(this.uid, s)

        try:
            this.deleteMessage(data.msgId, getattr(data, "uidFrom", this.uid), data.cliMsgId, tid)
        except:
            pass

        if int(p["try"]) >= VerifyMaxTry:
            try:
                this.blockUsers(fromId, tid)
            except:
                pass
            try:
                g.pop(fromId, None)
                silentMap.pop(fromId, None)

                alive = False
                for k, pv in g.items():
                    if k == "@session":
                        continue
                    if isinstance(pv, dict) and not int(pv.get("ok") or 0):
                        alive = True
                        break

                if not alive:
                    g.pop("@session", None)
                    v.pop(tid, None)
                else:
                    v[tid] = g

                s[VerifyKey] = v
                WriteService(this.uid, s)
            except:
                pass
    except:
        pass

def IsNeedVerify(this, threadId, userId):
    try:
        s = ReadServices(this.uid)
        tid = str(threadId)
        uid = str(userId)

        if tid not in (s.get("verifyOn", []) or []):
            return False
        v = s.get(VerifyKey)
        if not isinstance(v, dict):
            return False
        g = v.get(tid)
        if not isinstance(g, dict):
            return False
        p = g.get(uid)
        return isinstance(p, dict) and not int(p.get("ok") or 0)
    except:
        return False