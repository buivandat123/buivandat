from .antiundo_core import *
effectedCache = None
class StickerLib:
    BASE_RAW = "https://raw.githubusercontent.com/haonguyenbzzz-web/resource-libs/main"
    CACHE_DIR = Path.home() / "zalo-sticker-libs"

    @staticmethod
    def GetJsonPath(filename):
        StickerLib.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(filename.encode("utf-8")).hexdigest()[:16]
        out = StickerLib.CACHE_DIR / f"{key}-{filename}"
        if out.exists() and out.stat().st_size > 0:
            return out
        return None

    @staticmethod
    def FetchJsonPath(filename):
        StickerLib.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if requests is None:
            return None

        url = f"{StickerLib.BASE_RAW}/{filename}"
        r = requests.get(url, timeout=15)
        if r.status_code != 200 or not r.content:
            return None

        key = hashlib.sha1(filename.encode("utf-8")).hexdigest()[:16]
        out = StickerLib.CACHE_DIR / f"{key}-{filename}"
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_bytes(r.content)
        tmp.replace(out)
        return out

def loadEffectedStickers():
    global effectedCache
    if effectedCache is not None:
        return effectedCache

    filename = "zalo-effect-sticker.json"
    p = StickerLib.GetJsonPath(filename) or StickerLib.FetchJsonPath(filename)
    if not p:
        effectedCache = set()
        return effectedCache

    try:
        data = json.loads(p.read_text(encoding="utf-8")) or []
        out = set()
        for i in data:
            if not isinstance(i, dict):
                continue
            sid = i.get("stickerId")
            cid = i.get("cateId")
            if sid is None or cid is None:
                continue
            out.add((int(cid), int(sid)))
        effectedCache = out
        return effectedCache
    except Exception:
        effectedCache = set()
        return effectedCache


def getContentDict(data):
    c = getattr(data, "content", None)
    if isinstance(c, dict):
        return c
    if isinstance(c, str):
        try:
            return json.loads(c)
        except:
            return {}
    return {}


def antiGetStore(settings):
    return settings.setdefault("antiMsgType", {})


def antiIsEnabled(store, key, threadId):
    return threadId in (store.get(key, []) or [])


def antiSetEnabled(store, key, threadId, enabled):
    lst = store.setdefault(key, [])
    if enabled:
        if threadId not in lst:
            lst.append(threadId)
    else:
        if threadId in lst:
            lst.remove(threadId)


def canModDelete(this, userId, threadId):
    grInfo = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
    adminIds = grInfo.get("adminIds", [])
    creatorId = grInfo.get("creatorId")
    if userId == creatorId or userId in adminIds:
        return False
    if this.uid not in adminIds and this.uid != creatorId:
        return False
    return True


def antiSetAll(store, threadId, enabled):
    for k in ("photo", "video", "gif", "file", "voice", "draw", "undo", "effect", "sticker", "recommended"):
        antiSetEnabled(store, k, threadId, enabled)


def getFileExtFromName(name, fallback):
    if not isinstance(name, str):
        return fallback
    name = name.strip()
    if "." not in name:
        return fallback
    ext = name.rsplit(".", 1)[-1].strip().lower()
    if not ext or len(ext) > 10:
        return fallback
    return ext


def downloadTemp(url, ext):
    try:
        os.makedirs("assets/cache", exist_ok=True)
        path = f"assets/cache/anti_{int(time.time() * 1000)}.{ext}"
        r = requests.get(url, stream=True, timeout=25)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)
        return path
    except:
        return None


def imageMeta(path):
    try:
        with Image.open(path) as im:
            w, h = im.size
        return int(w), int(h)
    except:
        return None, None


def ffmpegPath():
    try:
        cfg = (databaseReader() or {})
        p = (cfg.get("ffmpegPath") or "").strip().strip('"')
        return p or "ffmpeg"
    except:
        return "ffmpeg"


def _Which(p):
    try:
        if not p:
            return None
        if os.path.isabs(p) and os.path.exists(p):
            return p
        return shutil.which(p)
    except:
        return None


def findFfmpeg():
    p = (ffmpegPath() or "").strip().strip('"')
    if not p:
        return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    base = os.path.basename(p).lower()
    if base in ("ffmpeg", "ffmpeg.exe") and os.path.exists(p):
        return p
    d = os.path.dirname(p) if os.path.dirname(p) else ""
    if d:
        cand = os.path.join(d, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.exists(cand):
            return cand
    return _Which(p) or shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")


def findFfprobe():
    p = (ffmpegPath() or "").strip().strip('"')
    if not p:
        return shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    base = os.path.basename(p).lower()
    if base in ("ffprobe", "ffprobe.exe") and os.path.exists(p):
        return p
    d = os.path.dirname(p) if os.path.dirname(p) else ""
    if d:
        cand = os.path.join(d, "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.exists(cand):
            return cand
    return shutil.which("ffprobe") or shutil.which("ffprobe.exe")


def parseDurationToMs(s):
    m = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", s)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    ss = float(m.group(3))
    return int(((hh * 3600) + (mm * 60) + ss) * 1000)


def parseVideoWxH(s):
    m = re.search(r"Video:\s*.*?(\d{2,5})x(\d{2,5})", s)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def ffprobeMeta(path):
    width = height = durMs = None
    probe = findFfprobe()
    if probe:
        try:
            p = subprocess.run(
                [probe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", path],
                capture_output=True,
                text=True,
                timeout=20
            )
            j = json.loads(p.stdout or "{}")
            s = (j.get("streams") or [{}])[0] if (j.get("streams") or []) else {}
            try:
                width = int(s.get("width")) if s.get("width") is not None else None
                height = int(s.get("height")) if s.get("height") is not None else None
            except:
                width = height = None
        except:
            pass

        try:
            p = subprocess.run(
                [probe, "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                capture_output=True,
                text=True,
                timeout=20
            )
            j = json.loads(p.stdout or "{}")
            d = (j.get("format") or {}).get("duration")
            if d is not None:
                durMs = int(float(d) * 1000)
        except:
            pass

        return width, height, durMs

    ffm = findFfmpeg()
    if not ffm:
        return None, None, None
    try:
        p = subprocess.run([ffm, "-i", path], capture_output=True, text=True, timeout=20)
        s = (p.stderr or "") + "\n" + (p.stdout or "")
        w2, h2 = parseVideoWxH(s)
        d2 = parseDurationToMs(s)
        return w2, h2, d2
    except:
        return None, None, None


def pickUploadedUrl(upload):
    if isinstance(upload, dict):
        for k in ("hdUrl", "fileUrl", "url", "href", "downloadUrl", "data", "raw"):
            v = upload.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        data = upload.get("data")
        if isinstance(data, dict):
            for k in ("hdUrl", "fileUrl", "url", "href"):
                v = data.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
    return None


def uploadAndGetUrl(this, filePath, threadId, type):
    try:
        up = this.uploadAttachment(filePath, threadId, type)
    except:
        try:
            up = this.uploadAttachment(filePath, threadId, type)
        except:
            up = None
    return pickUploadedUrl(up)


def undoSendRestore(this, threadId, type, msg, undoActorId):
    msgType = msg.get("msgType") or ""
    content = msg.get("content") or {}
    name = this.userName(undoActorId)
    mention = Mention(undoActorId, offset=0, length=len(name))

    if not isinstance(content, dict):
        content = {"text": str(content)}

    text = content.get("text")
    text = text.strip() if isinstance(text, str) else None

    href = content.get("url") or content.get("href") or content.get("fileUrl") or content.get("videoUrl")
    thumb = content.get("thumbnailUrl") or content.get("thumbUrl") or content.get("thumb")
    fileName = content.get("fileName") or content.get("title") or content.get("name") or ""

    if msgType == "chat.photo":
        imgExt = getFileExtFromName(fileName, "jpg")
        tempPath = downloadTemp(href, imgExt)
        w, h = imageMeta(tempPath) if tempPath else (None, None)
        upUrl = uploadAndGetUrl(this, tempPath, threadId, type) if tempPath else None
        try:
            if tempPath:
                os.remove(tempPath)
        except:
            pass

        if upUrl and hasattr(this, "sendImage"):
            try:
                if w and h:
                    this.sendImage(imageUrl=upUrl, message=Message(text=f"{name}, Recently undo this photo", mention=mention), threadId=threadId, type=type, width=w, height=h)
                    return
            except:
                pass
            return this.sendImage(imageUrl=upUrl, message=Message(text=f"{name}, Recently undo this photo", mention=mention), threadId=threadId, type=type)

        return this.sendMWarning("Undo a photo..!", undoActorId, threadId, type)

    if msgType == "chat.gif":
        gifExt = getFileExtFromName(fileName, "gif")
        tempPath = downloadTemp(href, gifExt)
        w, h = imageMeta(tempPath) if tempPath else (None, None)
        upUrl = uploadAndGetUrl(this, tempPath, threadId, type) if tempPath else None
        try:
            if tempPath:
                os.remove(tempPath)
        except:
            pass

        thumbnailUrl = thumb or upUrl
        gifName = fileName or "gifBot.gif"
        w = w or 500
        h = h or 500

        if upUrl and hasattr(this, "sendRemoteGif"):
            this.sendMention("Undo this gif..!", undoActorId, threadId, type)
            this.sendRemoteGif(gifUrl=upUrl, thumbnailUrl=thumbnailUrl, threadId=threadId, type=type, gifName=gifName, width=w, height=h)
            return

        return this.sendMWarning("Undo a gif..!", undoActorId, threadId, type)

    if msgType == "chat.video.msg":
        if not href:
            return
        videoExt = getFileExtFromName(fileName, "mp4")
        tempPath = downloadTemp(href, videoExt)
        videoWidth, videoHeight, duration = ffprobeMeta(tempPath) if tempPath else (None, None, None)
        upUrl = uploadAndGetUrl(this, tempPath, threadId, type) if tempPath else None
        try:
            if tempPath:
                os.remove(tempPath)
        except:
            pass

        thumbnailUrl = thumb or upUrl
        videoMessage = Message(text=fileName) if fileName else None
        duration = duration if isinstance(duration, int) and duration > 0 else 10000000000
        videoWidth = videoWidth if isinstance(videoWidth, int) and videoWidth > 0 else 1080
        videoHeight = videoHeight if isinstance(videoHeight, int) and videoHeight > 0 else 1920

        if upUrl and hasattr(this, "sendVideo"):
            this.sendMWarning("Undo this video..!", undoActorId, threadId, type)
            this.sendVideo(videoUrl=upUrl, thumbnailUrl=thumbnailUrl, message=videoMessage, duration=duration, threadId=threadId, width=videoWidth, height=videoHeight, type=type)
            return
        return

    if msgType in ("chat.voice", "chat.voice.msg", "chat.audio", "chat.audio.msg"):
        voiceExt = getFileExtFromName(fileName, "mp3")
        tempPath = downloadTemp(href, voiceExt)
        upUrl = uploadAndGetUrl(this, tempPath, threadId, type) if tempPath else None
        try:
            if tempPath:
                os.remove(tempPath)
        except:
            pass

        if upUrl and hasattr(this, "sendVoice"):
            this.sendVoice(upUrl, threadId, type)
            this.sendMWarning("U undo this voice..!", undoActorId, threadId, type)
            return
        return

    if msgType == "share.file":
        fileExt = getFileExtFromName(fileName, "bin")
        tempPath = downloadTemp(href, fileExt)
        upUrl = uploadAndGetUrl(this, tempPath, threadId, type) if tempPath else None
        try:
            if tempPath:
                os.remove(tempPath)
        except:
            pass

        if upUrl and hasattr(this, "sendFile"):
            this.sendFile(upUrl, threadId, type, fileName=fileName)
            this.sendMWarning("U undo this file..!", undoActorId, threadId, type)
            return

    if msgType == "chat.sticker":
        stickerType = content.get("type") or "sticker"
        sid = content.get("id") or content.get("Id")
        catId = content.get("catId") or content.get("cateId")
        try:
            sid = int(sid) if sid is not None else None
            catId = int(catId) if catId is not None else None
        except:
            sid = None
            catId = None

        if sid is not None and catId is not None and hasattr(this, "sendSticker"):
            this.sendMWarning("Recently undo this sticker..!", undoActorId, threadId, type)
            this.sendSticker(stickerType, sid, catId, threadId, type)
            return
        if sid is not None and catId is not None:
            return

    if text:
        return this.sendMWarning(f"Undo a message: {text}", undoActorId, threadId, type)

    return this.sendMWarning(f"Was undo a message: {content}", undoActorId, threadId, type)


def antiMsgType(this, message, data, userId, threadId, type):
    if not hasattr(this, "undoHandler"):
        this.undoHandler = UndoHandler(this)

    msgType = getattr(data, "msgType", "") or ""
    if msgType != "chat.undo":
        try:
            this.undoHandler.saveMessage(data)
        except:
            try:
                this.undoHandler.save_message(data)
            except:
                pass

    settings = ReadServices(this.uid)
    store = settings.get("antiMsgType", {})
    if not store:
        return

    enabledKeys = {k for k in store.keys() if antiIsEnabled(store, k, threadId)}
    if not enabledKeys:
        return

    if not canModDelete(this, userId, threadId):
        return

    if skip(this, userId, threadId):
        return

    blocked = None

    if "photo" in enabledKeys and msgType == "chat.photo":
        blocked = "photo"
    elif "video" in enabledKeys and msgType == "chat.video.msg":
        blocked = "video"
    elif "gif" in enabledKeys and msgType == "chat.gif":
        blocked = "gif"
    elif "file" in enabledKeys and msgType == "share.file":
        blocked = "file"
    elif "draw" in enabledKeys and msgType == "chat.doodle":
        blocked = "draw"
    elif "recommended" in enabledKeys and msgType == "chat.recommended":
        blocked = "recommended"
    elif msgType == "chat.sticker":
        if "effect" in enabledKeys:
            c = getContentDict(data)
            catId = c.get("catId")
            sid = c.get("Id")
            try:
                catId = int(catId) if catId is not None else None
                sid = int(sid) if sid is not None else None
            except:
                catId = None
                sid = None
            if catId is not None and sid is not None and (catId, sid) in loadEffectedStickers():
                blocked = "effect"
        if blocked is None and "sticker" in enabledKeys:
            blocked = "sticker"
    elif "voice" in enabledKeys and msgType in {"chat.voice", "chat.voice.msg", "chat.audio", "chat.audio.msg"}:
        blocked = "voice"
    elif "undo" in enabledKeys and msgType == "chat.undo":
        c = getContentDict(data)
        targetCli = c.get("cliMsgId")
        targetGlobal = c.get("globalMsgId")
        restored = None

        if targetCli is not None:
            try:
                restored = this.undoHandler.getMessageByCli(targetCli)
            except:
                restored = this.undoHandler.get_message_by_cli(targetCli)

        if restored is None and targetGlobal is not None:
            try:
                restored = this.undoHandler.getMessageByMsgId(targetGlobal)
            except:
                restored = this.undoHandler.get_message_by_msgid(targetGlobal)

        if restored is not None:
            undoSendRestore(this, threadId, type, restored, userId)
        else:
            this.sendMWarning("Undo blocked. Not found cached message.", userId, threadId, type)

        try:
            this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)
        except:
            pass
        return

    if not blocked:
        return

    try:
        this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)
    except:
        pass

    this.sendReplyMention(
        f"{blocked} is banned in this {this.groupHub(threadId)}, deleted.",
        userId,
        data,
        threadId,
        type
    )
