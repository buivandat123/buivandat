from dto.index import *
from functions.engine.data.data import ReadServices, WriteService

def isthisJoined(this, eventData, eventType):
    if eventType != GroupEventType.JOIN:
        return

    groupId = str(eventData.groupId or "").strip()
    if not groupId:
        return

    uid = str(this.uid)
    for m in (eventData.updateMembers or []):
        if str((m or {}).get("id")) == uid:
            break
    else:
        return

    s = ReadServices(this.uid)
    hub = this.groupHub(groupId)
    groupLink = str(getattr(hub, "link", "") or "").strip()
    if not groupLink:
        return

    if not bool(s.get("ignoreInvite", False)):
        return this.setMute(groupId)

    approved = s.get("approvedInvite") or []
    if groupLink in approved:
        approved.remove(groupLink)
        s["approvedInvite"] = approved
        WriteService(this.uid, s)
        return

    waiting = s.setdefault("waitingApprove", [])
    if groupLink not in waiting:
        waiting.append(groupLink)
        WriteService(this.uid, s)

    idx = waiting.index(groupLink) + 1
    creator = (hub.mod or {}).get("creator")
    if creator:
        this.sendMWarning(
            "I'm ignoring this invited, will wait for user approve",
            creator,
            groupId,
            ThreadType.GROUP
        )

    name = getattr(hub, "name", None) or groupId
    this.sendMCustom(
        "WAITING",
        "y",
        f"{idx} {name} is wait to approve to join",
        None,
        this.zfcloudId(),
        ThreadType.USER
    )

    this.leaveGroup(groupId)


def approveJoin(this, message, data, userId, threadId, type):
    t = (getattr(message, "text", None) or str(message or "")).strip()
    if not t.isdigit():
        return

    s = ReadServices(this.uid)
    waiting = s.get("waitingApprove") or []
    idx = int(t)
    if idx < 1 or idx > len(waiting):
        return

    groupLink = str(waiting[idx - 1] or "").strip()
    if not groupLink:
        return

    approved = s.get("approvedInvite") or []
    if groupLink not in approved:
        approved.append(groupLink)
    s["approvedInvite"] = approved

    waiting.pop(idx - 1)
    s["waitingApprove"] = waiting
    WriteService(this.uid, s)
    this.joinGroup(groupLink)