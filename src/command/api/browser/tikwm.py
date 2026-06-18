from functions.services.hook.media_hook.tiktok_hook import *

def HandleTikTokSendVideo(this, data, item, threadId, type, proxy=None):
    EnsureMediaCache(this)

    vid = str(item.get("id") or "")
    cache = (this.MediaCache.get(Platf, vid) if this.MediaCache else None) or {}

    fileUrl = CacheGet(cache, "fileUrl")
    thumbUrl = CacheGet(cache, "thumbnail")
    metaW = int(CacheGet(cache, "width", 1080) or 1080)
    metaH = int(CacheGet(cache, "height", 1920) or 1920)
    metaDur = int(CacheGet(cache, "duration", 0) or 0)
    desc = CacheGet(cache, "desc", "") or item.get("desc") or ""

    if fileUrl and not IsAlive(this, fileUrl):
        fileUrl = None

    if not fileUrl:
        tiktokUrl = MakeTikTokUrlFromId(vid)
        info = DownloadTikwmNoWatermark(tiktokUrl, proxy=proxy) if tiktokUrl else None
        if not info or info.get("type") != "video":
            this.sendMWarning("Video không hợp lệ hoặc là photo", None, threadId, type)
            return

        v = info.get("video") or {}
        videoUrl = v.get("noWatermarkUrl") or v.get("url")
        if not videoUrl:
            this.sendMWarning("Không có video url", None, threadId, type)
            return

        thumbUrl = v.get("cover") or Pick(item, "video", "cover", default="") or ""
        desc = info.get("desc") or item.get("desc") or ""

        os.makedirs("assets/cache", exist_ok=True)
        path = f"assets/cache/tk_{vid}_{int(time.time()*1000)}.mp4"
        try:
            DownloadFile(videoUrl, path, proxy=proxy, timeout=180)
        except:
            this.sendMWarning("Failed download", None, threadId, type)
            return

        meta = GetVideoMeta(GetFfmpegPath(this), path)
        metaW = int(meta.get("width") or 1080)
        metaH = int(meta.get("height") or 1920)
        metaDur = int(meta.get("duration") or 0)

        up = None
        try:
            up = this.uploadAttachment(path, threadId, type)
        finally:
            try:
                os.remove(path)
            except:
                pass

        fileUrl = up.get("fileUrl") if up else None
        if not fileUrl:
            this.sendMWarning("Upload video failed", None, threadId, type)
            return

        if this.MediaCache:
            this.MediaCache.set(
                Platf,
                vid,
                {"thumbnail": thumbUrl, "width": metaW, "height": metaH, "duration": metaDur, "desc": desc},
                fileUrl,
            )

    this.sendReaction(data, "", threadId, type, -1)
    this.sendVideo(
        fileUrl,
        thumbnailUrl=thumbUrl,
        duration=int(metaDur or 0),
        message=Message(text=desc),
        threadId=threadId,
        type=type,
        width=int(metaW or 1080),
        height=int(metaH or 1920),
    )
    this.sendReaction(data, "/-ok", threadId, type, 100000000)

def HandleTikTokSendAudio(this, data, item, threadId, type, proxy=None):
    EnsureMediaCache(this)

    vid = str(item.get("id") or "")
    cache = (this.MediaCache.get(Platf + "_audio", vid) if this.MediaCache else None) or {}

    voiceUrl = CacheGet(cache, "fileUrl")
    cardHd = CacheGet(cache, "cardHd")
    if voiceUrl and not IsAlive(this, voiceUrl):
        voiceUrl = None
    if cardHd and not IsAlive(this, cardHd):
        cardHd = None

    tiktokUrl = MakeTikTokUrlFromId(vid)
    info = GetVideoInfoTikwm(tiktokUrl, proxy=proxy) if tiktokUrl else None
    if not info:
        this.sendMWarning("Không lấy được info", None, threadId, type)
        return

    author = Pick(info, "author", "nickname", default="") or Pick(info, "author", "uniqueId", default="") or "TikTok"
    music = info.get("music") or {}
    audioUrl = music.get("url") or Pick(item, "music", "url", default="") or ""
    musicTitle = music.get("title") or Pick(item, "music", "title", default="") or "TikTok audio"
    cover = music.get("cover") or Pick(item, "video", "cover", default="") or ""

    if not audioUrl:
        this.sendMWarning("Không có audio url", None, threadId, type)
        return

    if not cardHd:
        os.makedirs("assets/cache", exist_ok=True)
        imgPath = f"assets/cache/tk_audio_{vid}_{int(time.time()*1000)}.png"
        try:
            draw_song_card(
                {
                    "title": musicTitle,
                    "artist": author,
                    "duration": "00:00:00",
                    "cover": cover,
                    "source": "TikTok",
                    "sourceIcon": "tiktokIcon.png",
                },
                imgPath,
            )
        except:
            draw_song_card(
                {
                    "title": musicTitle,
                    "artist": author,
                    "duration": "00:00:00",
                    "cover": None,
                    "source": "TikTok",
                    "sourceIcon": "tiktokIcon.png",
                },
                imgPath,
            )
        up = this.uploadImage(imgPath, threadId, type)
        cardHd = up.get("hdUrl") if up else None
        try:
            os.remove(imgPath)
        except:
            pass

    if not voiceUrl:
        os.makedirs("assets/cache", exist_ok=True)
        path = f"assets/cache/tk_audio_{vid}_{int(time.time()*1000)}.mp3"
        try:
            DownloadFile(audioUrl, path, proxy=proxy, timeout=180)
        except:
            this.sendMWarning("Failed download audio", None, threadId, type)
            return

        up = None
        try:
            up = this.uploadAttachment(path, threadId, type)
        finally:
            try:
                os.remove(path)
            except:
                pass

        voiceUrl = up.get("fileUrl") if up else None
        if not voiceUrl:
            this.sendMWarning("Upload voice failed", None, threadId, type)
            return

        if this.MediaCache:
            this.MediaCache.set(
                Platf + "_audio",
                vid,
                {"cardHd": cardHd, "title": musicTitle, "artist": author, "cover": cover},
                voiceUrl,
            )

    this.sendReaction(data, "", threadId, type, -1)
    if cardHd:
        this.sendImage(imageUrl=cardHd, message=Message(text=""), threadId=threadId, type=type, width=1600, height=600)
    this.sendVoice(voiceUrl, threadId, type)
    this.sendReaction(data, "/-ok", threadId, type, 100000000)

def ParseTikTokArgs(this, text):
    s = str(text or "").strip()
    p = str(getattr(this, "prefix", "") or "")
    if p and s.startswith(p):
        s = s[len(p):].lstrip()

    cmd = str(getattr(this, "commandName", "") or getattr(this, "rawCommand", "") or "tiktok").strip().lower()
    if cmd and s.lower().startswith(cmd):
        s = s[len(cmd):].lstrip()

    if s.startswith(cmd) and cmd and s[:len(cmd)].lower() == cmd:
        s = s[len(cmd):].lstrip()

    return s

def ParseSelectAudio(text):
    s = (text or "").strip().lower()
    p = s.split()
    if not p or not p[0].isdigit():
        return None
    n = int(p[0])
    if n <= 0:
        return None
    audio = len(p) >= 2 and p[1] in ("a", "audio", "mp3", "sound")
    return n, audio

def TikTokStrip(message, data):
    if isinstance(message, Message):
        text = message.text or ""
    else:
        text = str(message or "")
    text = text.strip()
    mentions = data.get("mentions") or []
    mentions = sorted(mentions, key=lambda x: x.get("pos", 0), reverse=True)
    for m in mentions:
        pos = m.get("pos", 0)
        ln = m.get("len", 0)
        if pos >= 0 and ln > 0:
            text = text[:pos] + text[pos + ln:]
    return text.strip()

def TikTokCommand(this, message, data, userId, threadId, type):
    if not hasattr(this, "tiktokStates"):
        this.tiktokStates = {}
    EnsureMediaCache(this)

    arg = ParseTikTokArgs(this, getattr(message, "text", message))
    if not arg:
        return this.sendMWarning(f"use {this.prefix}{this.rawCommand} keyword [limit]", userId, threadId, type)

    parts = arg.split()
    limit = 10
    if parts and parts[-1].isdigit():
        limit = max(1, min(30, int(parts[-1])))
        arg = " ".join(parts[:-1]).strip() or arg

    items = SearchTikwm(arg, limit)
    if not items:
        return this.sendMWarning("No result", userId, threadId, type)

    os.makedirs("assets/cache", exist_ok=True)
    imgPath = f"assets/cache/tk_list_{userId}_{int(time.time()*1000)}.png"
    okCard = True
    try:
        DrawTikTokListCard(items, imgPath)
    except:
        okCard = False
        imgPath = None

    w = W
    h = H
    if imgPath:
        try:
            im = Image.open(imgPath)
            w, h = im.size
            im.close()
        except:
            pass

    hd = None
    msg = None
    if imgPath:
        up = this.uploadImage(imgPath, threadId, type)
        hd = up.get("hdUrl") if up else None
        try:
            os.remove(imgPath)
        except:
            pass

    if hd:
        msg = this.sendImage(imageUrl=hd, message=Message(text=""), threadId=threadId, type=type, width=int(w), height=int(h))
    else:
        lines = []
        for i, it in enumerate(items, 1):
            st = it.get("stat") or {}
            lines.append(f"{i:02d}. {Short(it.get('desc',''),64)} | 👁 {FmtNum(st.get('playCount',0))} ❤ {FmtNum(st.get('diggCount',0))} 💬 {FmtNum(st.get('commentCount',0))}")
        msg = this.sendMWarning("\n".join(lines) + "\n\nReply số hoặc: 1 audio", userId, threadId, type)

    this.tiktokStates[userId] = {
        "items": items,
        "time": time.time(),
        "msgId": getattr(msg, "msgId", None),
        "cliMsgId": getattr(msg, "clientId", None),
        "threadId": threadId,
        "typeGr": type,
    }

    if not hasattr(this, "_tiktokCooldown"):
        this._tiktokCooldown = {}
    k = getattr(msg, "msgId", None)
    if k:
        this._tiktokCooldown[k] = True
        msgType = "chat.photo" if hd else "chat.text"
        msgObj = MessageObject(msgId=msg.msgId, cliMsgId=msg.clientId, msgType=msgType)

        def Loop():
            for i in range(Timeout, 0, -1):
                if not this._tiktokCooldown.get(k):
                    break
                this.sendMultiReaction(msgObj, "🕑", threadId, type, 102229, numreact=i)
                time.sleep(1)
                this.sendMultiReaction(msgObj, "", threadId, type, -1, numreact=i)
            this._tiktokCooldown.pop(k, None)

        threading.Thread(target=Loop, daemon=True).start()

def TikTokReply(this, message, data, userId, threadId, type):
    st = getattr(this, "tiktokStates", {}).get(userId)
    if not st:
        return
    if str(st.get("threadId")) != str(threadId):
        return
    if time.time() - st["time"] > Timeout:
        this.tiktokStates.pop(userId, None)
        this.sendMWarning("Selection expired", userId, threadId, type)
        return

    raw = message.text if isinstance(message, Message) else str(message or "")
    raw = (raw or "").strip()
    pfx = str(getattr(this, "prefix", "") or "")
    if pfx and raw.startswith(pfx):
        return

    sel = ParseSelectAudio(TikTokStrip(message, data))
    if not sel:
        return
    n, audio = sel

    items = st.get("items") or []
    if n < 1 or n > len(items):
        return

    key = st.get("msgId")
    if hasattr(this, "_tiktokCooldown") and key:
        this._tiktokCooldown[key] = False

    msgId = st.get("msgId")
    cliMsgId = st.get("cliMsgId")

    item = items[n - 1]
    this.tiktokStates.pop(userId, None)

    EnsureMediaCache(this)

    vid = str(item.get("id") or "")
    cacheKey = Platf + ("_audio" if audio else "")
    cache = (this.MediaCache.get(cacheKey, vid) if this.MediaCache else None) or {}
    cachedUrl = CacheGet(cache, "fileUrl")
    cachedOk = IsAlive(this, cachedUrl)

    waitMsg = None
    if not cachedOk:
        waitMsg = this.sendMCustom("WAITING", "y", "Wait, im hooking..!", userId, threadId, type)

    this.sendReaction(data, "🕑", threadId, type, 1000000023)

    def Run():
        try:
            if audio:
                HandleTikTokSendAudio(this, data, item, threadId, type)
            else:
                HandleTikTokSendVideo(this, data, item, threadId, type)
        finally:
            if waitMsg:
                try:
                    this.deleteMessage(waitMsg.msgId, this.uid, waitMsg.clientId, threadId)
                except:
                    pass

    threading.Thread(target=Run, daemon=True).start()

    if msgId and cliMsgId:
        try:
            this.deleteMessage(msgId, this.uid, cliMsgId, threadId)
        except:
            pass

def InitTimeoutTikTok(this, interval=1):
    if not hasattr(this, "tiktokStates"):
        this.tiktokStates = {}

    def Loop():
        while True:
            now = time.time()
            for uid, st in list(this.tiktokStates.items()):
                if now - st["time"] > Timeout:
                    this.tiktokStates.pop(uid, None)
                    try:
                        this.deleteMessage(st["msgId"], this.uid, st["cliMsgId"], st["threadId"])
                    except:
                        pass
                    this.sendMCustom("Timeout", "y", "Please search again", uid, st["threadId"], st["typeGr"])
            time.sleep(interval)

    threading.Thread(target=Loop, daemon=True).start()

dependencies = {
    "name": "tiktok",
    "permission": 0,
    "cooldown": 5,
    "description": "Videos on TikTok",
    "main": TikTokCommand,
}