from dto.index import *

def GroupList(this, message, data, userId, threadId, type, raw=None):
    stMap = getattr(this, "groupModifyStates", None)
    if stMap is None:
        stMap = {}
        this.groupModifyStates = stMap

    def Norm(s):
        return " ".join(str(s or "").lower().split())

    def ParseNums(s, mx):
        s = (s or "").replace(" ", "")
        if not s:
            return []
        out = []
        for x in s.split(","):
            if x.isdigit():
                v = int(x)
                if 1 <= v <= mx:
                    out.append(v)
        return sorted(set(out))

    prefix = str(getattr(this, "prefix", "") or "")

    def BuildCmd(text):
        t = (text or "").strip()
        if not t:
            return ""
        if prefix and t.startswith(prefix):
            return t
        parts = t.split()
        if not parts:
            return ""
        cmds = getattr(this, "commands", None)
        if isinstance(cmds, dict) and parts[0].lower() in cmds:
            return f"{prefix}{t}" if prefix else t
        return ""

    def ParseCmds(text):
        parts = [p.strip() for p in (text or "").split(",")]
        out = []
        for p in parts:
            c = BuildCmd(p)
            if c:
                out.append(c)
        return out

    def ExecCmdTo(gid, content):
        try:
            newData = data.copy() if isinstance(data, dict) else {}
            newData["content"] = content
            newData["mentions"] = []
            this.LoadCommands(message, newData, userId, gid, type)
        except:
            pass

    def SendList():
        gids = list((this.fetchAllGroups().gridVerMap or {}).keys())
        if not gids:
            return this.sendMWarning("Group list is empty", userId, threadId, type)

        items = [(str(g), str(this.groupHub(g).name or "Unknown")) for g in gids]
        items.sort(key=lambda x: (" ".join(x[1].lower().split()), x[0]))
        gids2 = [g for g, _ in items]
        names2 = [n for _, n in items]

        body = "\n".join(
            ["Group list"] +
            [f"{i}. {n}" for i, n in enumerate(names2, 1)]
        )
        sent = this.sendMSuccess(body, userId, threadId, type)
        if not sent:
            return

        stMap[f"{userId}:{threadId}"] = {
            "threadId": threadId,
            "msgId": getattr(sent, "msgId", None),
            "gids": gids2,
            "names": names2,
            "sel": [],
            "goto": None,
        }

    if raw is None:
        return SendList()

    raw = str(raw or "").strip()
    if not raw:
        return

    low = raw.lower().strip()
    cmd, _, rest = raw.partition(" ")
    cmdl = cmd.lower().strip()
    rest = rest.strip()

    key = f"{userId}:{threadId}"
    st = stMap.get(key)
    if not st or str(st.get("threadId")) != str(threadId):
        return

    sel = st.get("sel") or []
    gids = st.get("gids") or []
    names = st.get("names") or []
    pos = {g: i for i, g in enumerate(gids)}

    def AddIdx(i):
        gid = gids[i]
        if gid not in sel:
            sel.append(gid)
            st["sel"] = sel
            n = names[i]
        return this.sendMSuccess(f"Added: {n}", userId, threadId, type)

    def AddMany(idxs):
        a = 0
        for i in idxs:
            gid = gids[i]
            if gid not in sel:
                sel.append(gid)
                a += 1
        st["sel"] = sel
        return this.sendMSuccess(f"Added {a} groups", userId, threadId, type)

    def GotoExec(text):
        gid = st.get("goto")
        if not gid:
            return
        cmds = ParseCmds(text)
        if not cmds:
            return
        for c in cmds:
            ExecCmdTo(gid, c)

    if low == "exit all":
        stMap.pop(key, None)
        return this.sendMSuccess("Exit all sessions", userId, threadId, type)

    if cmdl == "exit":
        s = rest.replace(" ", "")
        if not s:
            stMap.pop(key, None)
            return this.sendMSuccess("Exit session", userId, threadId, type)
        if not sel:
            return this.sendMWarning("Session empty", userId, threadId, type)
        xs = [int(s)] if s.isdigit() else [int(x) for x in s.split(",") if x.isdigit()]
        xs = sorted({x for x in xs if 1 <= x <= len(sel)}, reverse=True)
        if not xs:
            return this.sendMWarning("Invalid session index", userId, threadId, type)
        for x in xs:
            sel.pop(x - 1)
        st["sel"] = sel
        g = st.get("goto")
        if g and g not in sel:
            st.pop("goto", None)
        return this.sendMSuccess("Session updated", userId, threadId, type)

    if cmdl == "session":
        if not sel:
            return
        lines = ["Selected groups:"]
        for i, gid in enumerate(sel, 1):
            j = pos.get(gid, -1)
            lines.append(f"{i}. {names[j] if j >= 0 else 'Unknown'}")
        return this.sendMSuccess("\n".join(lines), userId, threadId, type)

    if cmdl == "goto":
        if not sel:
            return this.sendMWarning("Pick group first.", userId, threadId, type)

        r = rest.replace(" ", "").lower()
        if not r:
            g = st.get("goto")
            if not g:
                return this.sendMSuccess("Exit visit group", userId, threadId, type)
            j = pos.get(g, -1)
            oli = names[j] if j >= 0 else 'Unknown'
            return this.sendMSuccess(f"Goto {oli}", userId, threadId, type)

        if r in ("off", "0", "none", "exit"):
            st.pop("goto", None)
            return this.sendMSuccess("Exit visit group", userId, threadId, type)

        if not r.isdigit():
            return this.sendMWarning("Invalid session index", userId, threadId, type)

        i = int(r)
        if i < 1 or i > len(sel):
            return this.sendMWarning("Invalid session index", userId, threadId, type)

        g = sel[i - 1]
        st["goto"] = g
        j = pos.get(g, -1)
        return this.sendMSuccess(f"Goto: {names[j] if j >= 0 else 'Unknown'}", userId, threadId, type)

    if cmdl == "send":
        if not rest:
            return this.sendMWarning("Message empty..!", userId, threadId, type)
        if not sel:
            return this.sendMWarning("Pick group first.", userId, threadId, type)
        d = 1 if len(sel) > 4 else 0
        for gid in sel:
            this.sendMessage(Message(text=rest), gid, type)
            if d:
                time.sleep(1)
        return

    if cmdl == "changelink":
        if not sel:
            return this.sendMWarning("Pick group first.", userId, threadId, type)
        d = 1 if len(sel) > 4 else 0
        ok = 0
        for gid in sel:
            if this.generateNewLink(gid):
                ok += 1
            if d:
                time.sleep(1)
        return this.sendMSuccess("Successful.." if ok else "No link", userId, threadId, type)

    if cmdl == "disablelink":
        if not sel:
            return this.sendMWarning("Pick group first.", userId, threadId, type)
        d = 1 if len(sel) > 4 else 0
        for gid in sel:
            this.disableLink(gid)
            if d:
                time.sleep(1)
        return this.sendMSuccess("Successful..", userId, threadId, type)

    q = getattr(data, "quote", None)
    qmsg = q.get("globalMsgId") if isinstance(q, dict) else getattr(q, "globalMsgId", None)
    okQuote = (qmsg and st.get("msgId") and str(qmsg) == str(st["msgId"]))

    if not okQuote:
        if st.get("goto"):
            return GotoExec(raw)
        if prefix and raw.startswith(prefix):
            return
        return

    if "->" in raw:
        lhs, rhs = raw.split("->", 1)
        selRaw = lhs.strip()
        cmdRaw = rhs.strip()

        cmds = ParseCmds(cmdRaw)
        if not cmds:
            return this.sendMWarning("Invalid command", userId, threadId, type)

        targets = []
        selLow = selRaw.lower()

        if selLow == "all":
            targets = gids[:]
        elif any(c.isdigit() for c in selRaw.replace(",", "")) and all((c.isdigit() or c in ", ") for c in selRaw):
            xs = ParseNums(selRaw, len(gids))
            if not xs:
                return this.sendMWarning("Invalid session index", userId, threadId, type)
            targets = [gids[x - 1] for x in xs]
        else:
            return this.sendMWarning("Invalid session index", userId, threadId, type)

        d = 1 if len(targets) > 4 else 0
        for gid in targets:
            for c in cmds:
                ExecCmdTo(gid, c)
            if d:
                time.sleep(1)
            tar = {len(targets)}
        return this.sendMSuccess(f"Executed {tar}", userId, threadId, type)

    if cmdl == "all":
        r = rest.strip()
        exNums = []
        exKey = ""
        if r.startswith("-"):
            r2 = r[1:].strip()
            if r2:
                if any(c.isdigit() for c in r2.replace(",", "")) and all((c.isdigit() or c in ", ") for c in r2):
                    exNums = ParseNums(r2, len(gids))
                else:
                    exKey = Norm(r2)

        if exNums:
            ex = set(x - 1 for x in exNums)
            st["sel"] = [gids[i] for i in range(len(gids)) if i not in ex]
            g = st.get("goto")
            if g and g not in st["sel"]:
                st.pop("goto", None)
            return this.sendMSuccess(f"Selected all except {len(ex)}", userId, threadId, type)

        if exKey:
            st["sel"] = [gids[i] for i, n in enumerate(names) if exKey not in Norm(n)]
            g = st.get("goto")
            if g and g not in st["sel"]:
                st.pop("goto", None)
            return this.sendMSuccess("Selected all", userId, threadId, type)

        st["sel"] = gids[:]
        return this.sendMSuccess(f"Selected all: {len(gids)} groups", userId, threadId, type)

    if "," in raw and all((c.isdigit() or c in ", ") for c in raw):
        xs = ParseNums(raw, len(gids))
        if not xs:
            return this.sendMWarning("Invalid group numbers", userId, threadId, type)
        return AddMany([x - 1 for x in xs])

    if "," in raw:
        ks = [Norm(x) for x in raw.split(",")]
        ks = [k for k in ks if k]
        if ks:
            hit = []
            for i, n in enumerate(names):
                nn = Norm(n)
                if any(k == nn or k in nn for k in ks):
                    hit.append(i)
            if hit:
                return AddMany(hit)

    if raw.isdigit():
        i = int(raw) - 1
        if i < 0 or i >= len(gids):
            return this.sendMWarning("Invalid group number", userId, threadId, type)
        return AddIdx(i)

    qn = Norm(raw)
    hit = [i for i, n in enumerate(names) if qn == Norm(n) or qn in Norm(n)]
    if len(hit) == 1:
        return AddIdx(hit[0])

    if len(hit) > 1:
        lines = ["Multiple groups matched:"] + [f"{i}. {names[j]}" for i, j in enumerate(hit, 1)] + ["", "Reply number to add, or all to add all."]
        sent = this.sendMSuccess("\n".join(lines), userId, threadId, type)
        if sent:
            st["gids"] = [gids[j] for j in hit]
            st["names"] = [names[j] for j in hit]
            st["msgId"] = getattr(sent, "msgId", None)
        return