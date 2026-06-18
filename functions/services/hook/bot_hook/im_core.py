from dto.index import *

def viewFriend(this):
    data = this.listFriendRequests().get("data") or {}
    items = data.get("recommItems") or []

    return [
        str(info.get("userId") or "")
        for i in items
        if isinstance(i, dict)
        for info in [i.get("dataInfo") or {}]
        if info.get("userId")
    ]

def initCheckFriendRequests(this):
    if getattr(this, "friendLoop", False):
        return
    this.friendLoop = True
    this.friendSeen = set()

    def loop():
        while True:
            time.sleep(30)
            s = ReadServices(this.uid)
            if not bool(s.get("autoAcceptFriend", False)):
                continue

            ids = viewFriend(this)
            for uid in ids:
                if not uid or uid in this.friendSeen:
                    continue
                this.friendSeen.add(uid)
                try:
                    this.acceptFriendRequest(uid)
                except:
                    pass

    threading.Thread(target=loop, daemon=True).start()

def DontcareMessage(this, message, data, userId, threadId, type):
    try:
        uid = str(userId or "").strip()
        if not uid:
            return

        s = ReadServices(this.uid) or {}
        dc = s.get("dontCare") or []
        if uid not in set(str(x) for x in dc if x):
            return

        msgId = getattr(data, "msgId", None)
        cliMsgId = getattr(data, "cliMsgId", None)
        if not msgId or not cliMsgId:
            return

        this.deleteMessage(msgId, uid, cliMsgId, threadId, True)

    except:
        return