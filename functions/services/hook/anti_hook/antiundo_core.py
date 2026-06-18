from dto.index import *

class UndoHandler:
    def __init__(this, owner_or_uid, max_messages=400):
        this.owner = owner_or_uid if hasattr(owner_or_uid, "uid") or hasattr(owner_or_uid, "MongoWorker") else None
        this.uid = str(getattr(owner_or_uid, "uid", owner_or_uid) or "")
        this.max_messages = max_messages
        this.messages = deque(maxlen=max_messages)
        this.lock = threading.Lock()
        this.eng = getattr(owner_or_uid, "MongoWorker", None) if this.owner is not None else None

    def _sql_ready(this):
        return bool(getattr(this.eng, "undoMongo", None))

    def save_message(this, data):
        msgtype = getattr(data, "msgType", "") or ""
        if msgtype == "chat.undo":
            return
        msgid = getattr(data, "msgId", "") or ""
        climsgid = getattr(data, "cliMsgId", "") or ""
        uidfrom = getattr(data, "uidFrom", "") or ""
        content = getattr(data, "content", None)

        content_dict = this._content_to_dict(content)

        item = {
            "msgId": str(msgid),
            "cliMsgId": str(climsgid),
            "uidFrom": str(uidfrom),
            "msgType": str(msgtype),
            "content": content_dict,
            "ts": int(time.time())
        }

        with this.lock:
            this.messages.append(item)
        if this._sql_ready():
            try:
                this.eng.undoMongo.Write(
                    this.uid,
                    item.get("msgId"),
                    item.get("cliMsgId"),
                    item.get("uidFrom"),
                    item.get("msgType"),
                    item.get("content"),
                    item.get("ts"),
                )
            except:
                pass

    def saveMessage(this, data):
        return this.save_message(data)

    def get_message_by_cli(this, cli_msg_id):
        target = str(cli_msg_id)
        with this.lock:
            for m in reversed(this.messages):
                if str(m.get("cliMsgId")) == target:
                    return m
        if this._sql_ready():
            try:
                return this.eng.undoMongo.GetByCli(this.uid, target)
            except:
                pass
        return None

    def get_message_by_msgid(this, msg_id):
        target = str(msg_id)
        with this.lock:
            for m in reversed(this.messages):
                if str(m.get("msgId")) == target:
                    return m
        if this._sql_ready():
            try:
                return this.eng.undoMongo.GetByMsgId(this.uid, target)
            except:
                pass
        return None

    def getMessageByCli(this, cli_msg_id):
        return this.get_message_by_cli(cli_msg_id)

    def getMessageByMsgId(this, msg_id):
        return this.get_message_by_msgid(msg_id)

    def _content_to_dict(this, content):
        if isinstance(content, dict):
            return content
        if isinstance(content, str):
            try:
                v = json.loads(content)
                if isinstance(v, dict):
                    return v
                return {"text": content}
            except:
                return {"text": content}
        try:
            d = {}
            for k in ("url", "href", "fileUrl", "videoUrl", "thumbnailUrl", "thumbUrl", "thumb", "title", "fileName", "name", "duration", "id", "catId", "Id", "catid", "params", "description"):
                if hasattr(content, k):
                    d[k] = getattr(content, k)
            if not d:
                return {"text": str(content)}
            return d
        except:
            return {"text": str(content)}
