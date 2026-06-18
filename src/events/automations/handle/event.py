from dto.index import *

def isNoLogEnabled():
    return os.getenv("ZBUG_NO_LOG", "0") == "1"

class EventLogger:
    def EventListener(this, eventType, eventData):
        if isNoLogEnabled():
            return False

        raw = "" if eventData is None else str(eventData)
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")

        gid = getattr(eventData, "groupId", None)
        sid = getattr(eventData, "sourceId", None)
        cid = getattr(eventData, "creatorId", None)

        gid = None if gid is None or str(gid) == "" else str(gid)
        sid = None if sid is None or str(sid) == "" else str(sid)
        cid = None if cid is None or str(cid) == "" else str(cid)

        meta = {
            "bot": str(getattr(this, "uid", "") or ""),
            "chat_type": "GROUP",
            "group_id": gid,
            "source_id": sid,
            "creator_id": cid,
        }

        et = str(eventType)
        gname = getattr(eventData, "groupName", None)
        gname = "" if gname is None else str(gname)
        cname = this.userName(sid)

        consoleText = (
            f"[{getattr(this, 'bot', '')}] - {et}\n"
            "Có Event nhóm mới\n"
            f"Tên nhóm: {gname} | Group Id: {gid or ''}\n"
            f"Người thực hiện: {cname} | Source Id: {sid or ''}"
        )

        ms = getattr(eventData, "updateMembers", None)
        if isinstance(ms, list) and ms:
            ids = []
            names = []
            for m in ms:
                if isinstance(m, dict):
                    mid = m.get("id")
                    dn = m.get("dName")
                else:
                    mid = getattr(m, "id", None)
                    dn = getattr(m, "dName", None)
                if mid is not None:
                    mid = str(mid)
                    if mid:
                        ids.append(mid)
                if dn is not None:
                    dn = str(dn)
                    if dn:
                        names.append(dn)
            if ids:
                consoleText += "\n" + f"Members: {', '.join(ids)}"
            if names:
                consoleText += "\n" + f"Names: {', '.join(names)}"

        logger.event(consoleText)

        eng = getattr(this, "MongoWorker", None)
        if not eng:
            return False

        if isinstance(eventData, dict):
            jsonText = json.dumps(eventData, ensure_ascii=False, default=str)
        elif hasattr(eventData, "__dict__"):
            jsonText = json.dumps(eventData.__dict__, ensure_ascii=False, default=str)
        else:
            jsonText = None

        ok = eng.eventMongo.Write(et, stamp, raw, meta=meta, jsonText=jsonText)
        eng.Flush(1.5)
        return bool(ok)