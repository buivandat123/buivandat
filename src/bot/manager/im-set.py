from functions.services.hook.bot_hook.im_core import *

def getMessageType(cliMsgType):
    if cliMsgType == 31: return "chat.voice"
    if cliMsgType == 32: return "chat.photo"
    if cliMsgType == 10: return "chat.sticker"
    if cliMsgType == 37: return "chat.doodle"
    if cliMsgType == 38: return "chat.link"
    if cliMsgType == 43: return "chat.location.new"
    if cliMsgType == 44: return "chat.video.msg"
    if cliMsgType == 46: return "share.file"
    if cliMsgType == 49: return "chat.gif"
    if cliMsgType == 52: return "chat.webcontent"
    if cliMsgType == 61: return "chat.webcontent.v2"
    return "webchat"

def iAm(this, message, data, userId, threadId, type):
    parts = (message.text or "").split()
    c = this.prefix + this.rawCommand
    if len(parts) < 2:
        return this.sendMWarning(textHelp(c).iAmHelp, userId, threadId, type)

    action = (parts[1] or "").strip().lower()
    arg = (parts[2].lower() if len(parts) > 2 else "")

    def Toggle(key, onMsg, offMsg, init=None):
        s = ReadServices(this.uid) or {}
        cur = bool(s.get(key, False))
        e = (not cur) if not arg else (arg == "on") if arg in ("on", "off") else None
        if e is None:
            return
        s[key] = e
        WriteService(this.uid, s)
        if init:
            try: init()
            except: pass
        return this.sendMSuccess(onMsg if e else offMsg, userId, threadId, type)

    if action == "friend":
        return Toggle("autoAcceptFriend", "I'm friendly now", "I'm not friendly..", lambda: initCheckFriendRequests(this))
    
    if action == "lazy":
        return Toggle("undoMode", "I'm lazy to undo, send me /-heart to undo", "Uhhh, I'm focus :)")

    if action == "ignore":
        return Toggle("ignoreInvite",
            "I'm now ignore box invited to wait owner approve!",
            "I'm no longer ignore box invited to wait owner approve!"
        )
    
    if action == "vietnamese":
        return Toggle("vi", "Tui là một người Việt Nam", "I'm still a Vietnamese but I wanna say English")

    if action == "ghost":
        return Toggle("ghostStatus", "I'm a ghost bot..!", "I'm not a ghost bot, just normally:3")
    
    if action == "learn":
        Toggle("imLearning", "I'm learning to says", "I'm lazy, will not learn anything now")
        if arg == "now":
            quoted = data.quote
            return 
        return 

    if action == "dontcare":
        op = arg if arg in ("add", "remove", "rm", "del", "toggle", "list", "clear") else "toggle"
        s = ReadServices(this.uid) or {}
        dc = s.setdefault("dontCare", [])
        cur = set(str(x) for x in dc if x)

        def Save():
            s["dontCare"] = [x for x in dc if x]
            WriteService(this.uid, s)

        if op == "list":
            if not dc:
                return
            out = ["Hated:", ""] + [f"{i}. {this.userName(uid)}" for i, uid in enumerate(dc, 1)]
            return this.sendMMessage("\n".join(out).strip(), userId, threadId, type)

        if op == "clear":
            if not dc:
                return
            s["dontCare"] = []
            WriteService(this.uid, s)
            return this.sendMSuccess("Cleared hated", userId, threadId, type)

        uids = [str(x or "").strip() for x in (this.extractUids(data) or [])]
        uids = [x for x in uids if x]
        if not uids:
            return this.sendMWarning("No target", userId, threadId, type)

        added = removed = 0
        for uid in uids:
            has = uid in cur
            add = (op == "add") or (op == "toggle" and not has)
            rm = (op in ("remove", "rm", "del")) or (op == "toggle" and has)

            if add and not has:
                dc.append(uid); cur.add(uid); added += 1
            elif rm and has:
                cur.remove(uid)
                try: dc.remove(uid)
                except: pass
                removed += 1

        if added or removed:
            Save()

        if len(uids) == 1:
            uid = uids[0]
            name = this.userName(uid)
            if added: return this.sendMSuccess(f"I dont care {name} say anything", userId, threadId, type)
            if removed: return this.sendMSuccess(f"Listen to: {name}", userId, threadId, type)
            return this.sendMSuccess(f"Already my mind for {name} I wouldnt change anything!", userId, threadId, type)

        return this.sendMSuccess(f"Hmm, I think I should: don't care {added} and listen for {removed}", userId, threadId, type)

dependencies = {
    "name": "im",
    "permission": 4,
    "cooldown": 3,
    "description": "My setting for bot",
    "main": iAm
}