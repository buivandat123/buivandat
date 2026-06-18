from .group_modify.listGroup import *

def findMember(this, threadId, memberName):
    info = this.fetchGroupInfo(threadId).gridInfoMap[threadId]
    memList = [
        x[:-2] if isinstance(x, str) and x.endswith("_0") else x
        for x in (info.get("memVerList") or [])
    ]

    r = this.getGroupMember(threadId) or {}
    profiles = r.get("profiles") or {}

    q = [
        " ".join(x.strip().lower().split())
        for x in str(memberName or "").split(",")
        if x.strip()
    ]
    q = list(dict.fromkeys(q))

    rows = []
    seen = set()
    for uid in memList:
        uid = str(uid or "").strip()
        if not uid or uid in seen:
            continue
        p = profiles.get(uid)
        if not p:
            continue
        name = (p.get("displayName") or p.get("zaloName") or uid).strip()
        dn = " ".join(str(p.get("displayName") or "").lower().split())
        zn = " ".join(str(p.get("zaloName") or "").lower().split())
        if (not q) or any(k in dn or k in zn for k in q):
            seen.add(uid)
            rows.append((uid, name))
    return rows


def ApplyMemberReplyAction(this, message, data, userId, threadId, type):
    stMap = getattr(this, "groupModifyStates", None)
    if stMap is None:
        stMap = {}
        this.groupModifyStates = stMap

    q = getattr(data, "quote", None)
    qmsg = q.get("globalMsgId") if isinstance(q, dict) else getattr(q, "globalMsgId", None)
    if not qmsg:
        return None

    key = f"{userId}:{threadId}"
    st = stMap.get(key)
    if not st or str(st.get("threadId")) != str(threadId):
        return None

    okQuote = (st.get("msgId") and str(qmsg) == str(st["msgId"]))
    if not okQuote:
        return None

    txt = (message.text if isinstance(message, Message) else str(message or "")).strip()
    if not txt:
        return None

    head, tail = (txt.split(None, 1) + [""])[:2]
    action = head.lower().strip()
    pick = tail.strip()
    if action not in ("kick", "block"):
        return None

    rows = st.get("rows") or []
    if not rows:
        return this.sendMFailed("Reply dưới list/find trước", userId, threadId, type)

    s = pick.replace(" ", "")
    toks = [x for x in s.split(",") if x]
    if not toks:
        return this.sendMWarning("Ví dụ: kick 1,2 hoặc kick Nhật,Nguyên", userId, threadId, type)

    idxs = []
    keys = []
    for t in toks:
        if t.isdigit():
            idxs.append(int(t))
        else:
            keys.append(" ".join(t.lower().split()))

    members = []
    seen = set()

    for i in sorted(set(idxs)):
        j = i - 1
        if 0 <= j < len(rows):
            uid = rows[j][0]
            if uid not in seen:
                seen.add(uid)
                members.append(uid)

    if keys:
        for uid, name in rows:
            n = " ".join(str(name or "").lower().split())
            if any(k in n for k in keys):
                if uid not in seen:
                    seen.add(uid)
                    members.append(uid)

    if not members:
        return this.sendMFailed("Không có mục tiêu", userId, threadId, type)

    try:
        if action == "kick":
            this.kickUsers(members, threadId)
        else:
            this.blockUsers(members, threadId)
        return
    except:
        return this.sendMFailed(f"", userId, threadId, type)

def groupSettings(parts, this, message, data, userId, threadId, type):
    groupInfo = this.groupHub(threadId).settings
    lockChat = groupInfo.get("lockSendMsg")
    subCommand = parts[2].lower()
    
    if subCommand == "lock":
        if lockChat == 0:
            this.changeGroupSetting(threadId, lockSendMsg=1)
            return this.sendMSuccess(f"Locked chat in {this.groupHub(threadId).en} {this.groupHub(threadId).name}", userId, threadId, type)
        else:
            this.changeGroupSetting(threadId, lockSendMsg=0)
            return this.sendMSuccess(f"Unlocked chat in {this.groupHub(threadId).en} {this.groupHub(threadId).name}", userId, threadId, type)
    if subCommand == "ign-raid":
        this.changeGroupSetting(groupId=threadId, defaultMode="anti-raid", lockSendMsg=1)
        this.sendMSuccess(f"Applied anti-raid settings to {this.groupHub(threadId).en} {this.groupHub(threadId).name}", userId, threadId, type)
        return 

def groupManagerCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    c = this.prefix + this.rawCommand

    if len(parts) < 2:
        return this.sendMWarning(textHelp(c).groupModify, userId, threadId, type)

    sub = parts[1].lower()

    if sub == "list":
        return GroupList(this, message, data, userId, threadId, type)
    
    if sub == "name":
        if len(parts)<3:
            return this.sendMWarning("Type name before the command..", userId, threadId, type)
        nameGroup = " ".join(parts[2:])
        this.sendMSuccess(f"Changed {this.groupHub(threadId).name} to {nameGroup}", userId, threadId, type)
        this.changeGroupName(nameGroup, threadId)
        return
    
    if sub in ("settings", "stg"):
        if len(parts)<3:
            this.sendMWarning(f"""Please add a setting before the command
    {c} settings lock: Lock or unlock chat in the {this.groupHub(threadId).en}
    {c} settings ign-raid: Anti raid for the {this.groupHub(threadId).en}""", userId, threadId, type)
            return
        groupSettings(parts, this, message, data, userId, threadId, type)
        return

    if sub == "find":
        if len(parts) < 3:
            return this.sendMWarning("Enter the member name to find", userId, threadId, type)

        q = " ".join(parts[2:])
        rows = findMember(this, threadId, q)
        if not rows:
            return this.sendMFailed("Not found", userId, threadId, type)

        body = "\n".join(["Members:"] + [f"{i}. {name}" for i, (_uid, name) in enumerate(rows, 1)])
        sent = this.sendMSuccess(body, userId, threadId, type)
        if not sent:
            return

        stMap = getattr(this, "groupModifyStates", None)
        if stMap is None:
            stMap = {}
            this.groupModifyStates = stMap

        stMap[f"{userId}:{threadId}"] = {
            "threadId": threadId,
            "msgId": getattr(sent, "msgId", None),
            "rows": rows
        }
        return sent

    return this.sendMWarning(textHelp(c).groupModify, userId, threadId, type)


def GroupModifyReply(this, message, data, userId, threadId, type):
    r = ApplyMemberReplyAction(this, message, data, userId, threadId, type)
    if r is not None:
        return r

    raw = (message.text if isinstance(message, Message) else str(message or "")).strip()
    if not raw:
        return
    return GroupList(this, message, data, userId, threadId, type, raw=raw)


dependencies = {
    "name": "group",
    "permission": 3,
    "cooldown": 3,
    "description": "Group Manager",
    "main": groupManagerCommand
}