from dto.index import *
from functions.services.artistcore.menuDraw import draw_menu

MenuTimeout = 180
PerPage = 12

RolePermissionMap = {
    "user": 0, "member": 0,
    "mod": 1, "moderator": 1,
    "admin": 2, "adminbot": 2,
    "owner": 3, "high": 3,
    "root": 4
}

def removeAccent(text):
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")

def MenuCommand(this, message, data, userId, threadId, type):
    if not hasattr(this, "menuStates"):
        this.menuStates = {}

    def loadCommands():
        p = f"assets/storage/{this.uid}/Command.json"
        d = jsonLoader(p, {"command": []})
        out = []
        for c in d.get("command", []):
            out.append({
                "name": (c.get("name") or ""),
                "description": (c.get("description") or ""),
                "permission": int(c.get("permission", 0) or 0),
                "cooldown": int(c.get("cooldown", 0) or 0),
                "alias": c.get("alias") or []
            })
        out.sort(key=lambda x: (x.get("name") or "").lower())
        return out

    def safeDel(path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def delMsg(st):
        try:
            if st and st.get("msgId") and st.get("cliMsgId"):
                this.deleteMessage(st["msgId"], this.uid, st["cliMsgId"], threadId)
        except Exception:
            pass

    def sendPage(cmds, page, totalPage):
        fn = f"assets/cache/menu_{threadId}_p{page}_{int(time.time()*1000)}.png"
        w, h = draw_menu(removeAccent(this.bot), cmds[(page - 1) * PerPage: (page - 1) * PerPage + PerPage], fn, page=page, total_page=totalPage)
        up = this.uploadImage(fn, threadId, type) or {}
        safeDel(fn)
        hd = up.get("hdUrl")
        if not hd:
            return None, None, None
        name = this.userName(userId)
        sent = this.sendImage(
            imageUrl=hd,
            message=Message(text="", mention=Mention(userId, length=len("@Member"), offset=0)),
            threadId=threadId,
            type=type,
            width=w,
            height=h
        )
        return sent, w, h

    def allText(cmds):
        lines = []
        for i, c in enumerate(cmds, 1):
            n = (c.get("name") or "").strip()
            d = (c.get("description") or "").strip()
            p = int(c.get("permission") or 0)
            cd = int(c.get("cooldown") or 0)
            a = c.get("alias") or []
            lines.append(f"{i}. {n}{(' - alias: ' + ', '.join(a)) if a else ''}")
        return "\n".join(lines).strip()

    parts = (message.text or "").strip().split()
    cmds = loadCommands()

    perm = None
    pageArg = None
    if len(parts) >= 2:
        a1 = (parts[1] or "").strip().lower()
        if a1 == "all":
            return this.sendMSuccess(allText(cmds), userId, threadId, type)
        if a1:
            perm = RolePermissionMap.get(a1)
    if len(parts) >= 3:
        a2 = (parts[2] or "").strip()
        if a2.isdigit():
            pageArg = int(a2)

    if isinstance(perm, int):
        cmds = [c for c in cmds if int(c.get("permission") or 0) == perm]
        if not cmds:
            return this.sendMention(f"No commands for permission {perm}", userId, threadId, type)

    total = len(cmds)
    totalPage = max(1, (total + PerPage - 1) // PerPage)

    key = f"{userId}:{threadId}"
    st = this.menuStates.get(key)
    page = int(st.get("page", 1)) if st else 1
    if isinstance(pageArg, int):
        page = pageArg
    if page < 1:
        page = 1
    if page > totalPage:
        page = totalPage

    if st:
        delMsg(st)

    sent, _, _ = sendPage(cmds, page, totalPage)

    this.menuStates[key] = {
        "commands": cmds,
        "page": page,
        "total_page": totalPage,
        "time": time.time(),
        "msgId": getattr(sent, "msgId", None),
        "cliMsgId": getattr(sent, "clientId", None),
        "threadId": threadId
    }

def MenuReply(this, message, data, userId, threadId, type):
    if not hasattr(this, "menuStates"):
        this.menuStates = {}

    

    def delMsg(st):
        try:
            if st and st.get("msgId") and st.get("cliMsgId"):
                this.deleteMessage(st["msgId"], this.uid, st["cliMsgId"], threadId)
        except Exception:
            pass

    def safeDel(path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def sendPage(cmds, page, totalPage):
        fn = f"assets/cache/menu_{threadId}_p{page}_{int(time.time()*1000)}.png"
        w, h = draw_menu(removeAccent(this.bot), cmds[(page - 1) * PerPage: (page - 1) * PerPage + PerPage], fn, page=page, total_page=totalPage)
        up = this.uploadImage(fn, threadId, type) or {}
        safeDel(fn)
        hd = up.get("hdUrl")
        if not hd:
            return None
        name = this.userName(userId)
        return this.sendImage(
            imageUrl=hd,
            message=Message(text=f"{name}", mention=Mention(userId, offset=0, length=len(name))),
            threadId=threadId,
            type=type,
            width=w,
            height=h
        )

    key = f"{userId}:{threadId}"
    st = this.menuStates.get(key)
    if not st:
        return

    if time.time() - float(st.get("time", 0) or 0) > MenuTimeout:
        delMsg(st)
        this.menuStates.pop(key, None)
        return

    txt = message
    q = getattr(data, "quote", None)
    qmsg = q.get("globalMsgId") if isinstance(q, dict) else getattr(q, "globalMsgId", None)
    if qmsg and st.get("msgId") and str(qmsg) != str(st.get("msgId")):
        return

    if txt == "out":
        delMsg(st)
        this.menuStates.pop(key, None)
        return

    cmds = st.get("commands") or []
    totalPage = int(st.get("total_page") or 1)
    page = int(st.get("page") or 1)

    if txt == "next":
        page = min(totalPage, page + 1)
    elif txt in ("pre", "prev"):
        page = max(1, page - 1)
    elif qmsg and txt.isdigit():
        page = max(1, min(totalPage, int(txt)))
    else:
        return

    delMsg(st)
    sent = sendPage(cmds, page, totalPage)
    if not sent:
        this.menuStates.pop(key, None)
        return

    st["page"] = page
    st["time"] = time.time()
    st["msgId"] = getattr(sent, "msgId", None)
    st["cliMsgId"] = getattr(sent, "clientId", None)
    st["threadId"] = threadId

def InitTimeoutMenu(this, interval=2):
    if not hasattr(this, "menuStates"):
        this.menuStates = {}

    def loop():
        while True:
            now = time.time()
            for k, st in list(this.menuStates.items()):
                if now - float(st.get("time", 0) or 0) > MenuTimeout:
                    try:
                        if st.get("msgId") and st.get("cliMsgId") and st.get("threadId"):
                            this.deleteMessage(st["msgId"], this.uid, st["cliMsgId"], st["threadId"])
                    except Exception:
                        pass
                    this.menuStates.pop(k, None)
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True).start()

dependencies = {
    "name": "menu",
    "permission": 0,
    "cooldown": 7,
    "description": "Show bot commands",
    "main": MenuCommand
}
