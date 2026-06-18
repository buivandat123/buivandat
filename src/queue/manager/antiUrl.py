from dto.index import *

UrlPattern = re.compile(
    r"(https?://|www\.|[a-z0-9-]+\.(com|vn|net|org|io|me|co|xyz|site|online|info|biz|gg|tv|app|dev|link|cc|id|jp|kr|us|uk|asia)\b)",
    re.IGNORECASE
)

def ScanQr(ImagePath):
    img = Image.open(ImagePath)
    for obj in decode(img):
        try:
            return obj.data.decode("utf-8", "ignore")
        except:
            return None
    return None

def HasUrl(Text):
    if not Text or not isinstance(Text, str):
        return False
    return UrlPattern.search(Text) is not None

def DownloadToFile(Url, Path):
    try:
        r = requests.get(Url, timeout=10)
        if r.status_code != 200:
            return False
        with open(Path, "wb") as f:
            f.write(r.content)
        return True
    except:
        return False

def antiUrlMessage(this, message, data, userId, threadId, type):
    if not hasattr(this, "_antiUrlLog"):
        this._antiUrlLog = {}

    settings = ReadServices(this.uid)
    antiurl = settings.get("antiUrl", [])
    if threadId not in antiurl:
        return

    grInfo = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
    adminIds = set(grInfo.get("adminIds", []) or [])
    creatorId = grInfo.get("creatorId")

    if this.uid not in adminIds and this.uid != creatorId:
        return
    if userId == creatorId or userId in adminIds:
        return
    if skip(this, userId, threadId):
        return

    msgType = getattr(data, "msgType", "")
    isLink = False

    if msgType == "chat.recommended":
        isLink = True

    elif msgType == "chat.photo":
        content = getattr(data, "content", None) or {}
        href = content.get("href") if isinstance(content, dict) else None
        if href:
            cachePath = "assets/cache/qr.png"
            if DownloadToFile(href, cachePath):
                qrText = ScanQr(cachePath)
                if HasUrl(qrText):
                    isLink = True

    else:
        content = getattr(data, "content", "")
        if isinstance(content, dict):
            content = content.get("text") or content.get("content") or ""
        if HasUrl(content):
            isLink = True

    if not isLink:
        return

    try:
        this.sendMWarning(
            f"{this.groupHub(threadId).name} {this.groupHub(threadId)} is blocked link messages..!",
            userId, threadId, type
        )
        this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)
    except:
        pass

    key = (threadId, userId)
    now = time.time()

    logs = this._antiUrlLog.get(key, [])
    logs = [t for t in logs if now - t <= 300]
    logs.append(now)
    this._antiUrlLog[key] = logs

    if len(logs) >= 3:
        this.blockUsers(userId, threadId)
        this._antiUrlLog.pop(key, None)

def antiUrlCommand(this, message, data, userId, threadId, type):
    parts = message.text.strip().split()

    settings = ReadServices(this.uid)
    antiurl = settings.setdefault("antiUrl", [])
    enabled = threadId in antiurl

    if len(parts) < 2:
        enabled = not enabled
    else:
        action = parts[1].lower()
        if action == "on":
            enabled = True
        elif action == "off":
            enabled = False
        else:
            return

    if enabled:
        if threadId not in antiurl:
            antiurl.append(threadId)
    else:
        if threadId in antiurl:
            antiurl.remove(threadId)

    WriteService(this.uid, settings)
    this.sendMSuccess(f"Anti URL is now {'enabled' if enabled else 'disabled'}.", userId, threadId, type)

dependencies = {
    "name": "antiurl",
    "permission": 2,
    "description": "Anti message has url or qr has url",
    "cooldown": 5,
    "main": antiUrlCommand
}