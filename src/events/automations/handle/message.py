from dto.index import *

def isNoLogEnabled():
    return os.getenv("ZBUG_NO_LOG", "0") == "1"

def logMessage(this, logger, *, chat_type, message, data, forward):
    if isNoLogEnabled():
        return False

    uid = int(getattr(data, "uidFrom", 0) or 0)
    if uid == 0:
        return False

    msgType = str(getattr(data, "msgType", "") or "")
    if msgType in ("chat.reaction", "chat.undo", "chat.delete"):
        return False

    userName = this.userName(uid)
    gid = ""
    gname = ""
    if str(chat_type or "") == "GROUP":
        gid = str(getattr(data, "idTo", "") or "")
        gname = this.groupHub(gid).name if gid else ""

    raw = "" if message is None else str(message)
    contentText = raw
    storeText = raw
    ref = None

    if msgType == "chat.photo":
        try:
            params = json.loads(((getattr(data, "content", None) or {}).get("params")) or "{}")
        except:
            params = {}
        ref = (getattr(data, "content", None) or {}).get("href")
        contentText = "Sticker" if params.get("pStickerType") == 1 else "Photo"
        if ref:
            contentText += f"\nLink: {ref}"
        storeText = "" if ref is None else str(ref)

    p = getattr(getattr(data, "paramsExt", None), "platformType", None)
    platform = {0: "Zalo APP", 1: "Zalo Web", 2: "Zalo PC"}.get(p, "Unknown")

    cliMsgId = getattr(data, "cliMsgId", None)
    if cliMsgId is None:
        cliMsgId = getattr(data, "cliMsgID", None)
    cliMsgId = "" if cliMsgId is None else str(cliMsgId)

    meta = {
        "bot": str(getattr(this, "uid", "") or ""),
        "chat_type": str(chat_type or ""),
        "user_name": userName,
        "user_id": str(uid),
        "msg_type": msgType,
        "forward": bool(forward),
        "prefix": "CHAT",
        "platform": platform,
    }
    if gid:
        meta["group_id"] = gid
        meta["group_name"] = gname or None
    if ref:
        meta["ref"] = ref
    if cliMsgId:
        meta["cliMsgId"] = cliMsgId

    if meta["chat_type"] == "GROUP":
        viewText = (
            "Có Mesage nhóm mới:\n"
            f"Tên Nhóm: {gname} | Group ID: {gid}\n"
            f"Người Gửi: {userName} | Sender ID: {uid}\n"
            f"Nội Dung: {contentText}\n"
            f"    [ {platform} ]"
        )
    else:
        viewText = (
            "Có Mesage Riêng tư mới:\n"
            f"Người Gửi: {userName} | Sender ID: {uid}\n"
            f"Nội Dung: {contentText}\n"
            f"    [ {platform} ]"
        )
    if ref:
        viewText += f"\n→ {ref}"

    logger.fnLogger("message", viewText, kindLog=None, meta=meta)

    eng = getattr(this, "MongoWorker", None)
    if not eng:
        return False

    try:
        ok = eng.messageMongo.Write("message", "MESSAGE", logger.Unixstamp(), storeText, meta=meta)
        try:
            eng.Flush(1.5)
        except:
            pass
        return bool(ok)
    except:
        return False