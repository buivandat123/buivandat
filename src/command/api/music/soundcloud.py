from functions.services.hook.music_hook.soundcloudApi import *
from functions.engine.data.data import ReadServices, WriteService
from functions.services.artistcore.searchSongs import DrawSongsListCard, W, H
from functions.services.artistcore.songsCard import draw_song_card
from functions.engine.data.mediaEngine import MediaCache
from src.command.chatBot.special.sticker import CreateStickerUrl, MaxStickerSize, GetMediaWh
from src.command.api.music._shared import (
    FmtDuration,
    EnsureMediaCache as SharedEnsureMediaCache,
    CacheGet as SharedCacheGet,
    IsAlive as SharedIsAlive,
    ParseCommandArgs,
    StripSelectionText,
    ToggleSpinDisk,
    StartSelectionCooldown,
    InitSelectionTimeout,
)

Platf = "soundcloud"
Timeout = 120

def Fmt(t):
    return FmtDuration(t)

def EnsureMediaCache(this):
    return SharedEnsureMediaCache(this)

def GetCacheValue(cache, key, default=None):
    return SharedCacheGet(cache, key, default)

def IsAlive(this, url):
    return SharedIsAlive(this, url)

def GetSongCache(this, song):
    EnsureMediaCache(this)
    sid = str(song.get("id") or "")
    cache = (this.MediaCache.get(Platf, sid) if this.MediaCache else None) or {}

    data = {
        "sid": sid,
        "voiceUrl": GetCacheValue(cache, "fileUrl"),
        "cardHd": GetCacheValue(cache, "cardHd"),
        "stickerFileUrl": GetCacheValue(cache, "stickerFileUrl") or GetCacheValue(cache, "stickerUrl"),
        "stickerZaloStk": GetCacheValue(cache, "stickerZaloStk"),
        "stickerW": int(GetCacheValue(cache, "stickerW", 512) or 512),
        "stickerH": int(GetCacheValue(cache, "stickerH", 512) or 512),
    }

    if not IsAlive(this, data["voiceUrl"]):
        data["voiceUrl"] = None
    if not IsAlive(this, data["cardHd"]):
        data["cardHd"] = None
    if not IsAlive(this, data["stickerFileUrl"]):
        data["stickerFileUrl"] = None
        data["stickerZaloStk"] = None
    if data["stickerZaloStk"] and not IsAlive(this, data["stickerZaloStk"].split("?", 1)[0]):
        data["stickerZaloStk"] = None

    return data

def UploadSongCard(this, song, threadId, type, prefix):
    os.makedirs("assets/cache", exist_ok=True)
    path = f"assets/cache/{prefix}_{song.get('id')}_{int(time.time() * 1000)}.png"
    payload = {
        "title": song.get("title", "Unknown"),
        "artist": song.get("artist", "Unknown"),
        "duration": Fmt(song.get("duration")),
        "cover": song.get("cover"),
        "source": "SoundCloud",
        "sourceIcon": "soundcloudIcon.png"
    }

    try:
        try:
            draw_song_card(payload, path)
        except:
            payload["cover"] = None
            draw_song_card(payload, path)

        up = this.uploadImage(path, threadId, type)
        return up.get("hdUrl") if up else None
    finally:
        try:
            os.remove(path)
        except:
            pass

def UploadSpinSticker(this, coverUrl):
    os.makedirs("assets/cache", exist_ok=True)
    path = f"assets/cache/sc_spin_{int(time.time() * 1000)}.webp"

    try:
        CreateStickerUrl(
            coverUrl,
            path,
            xp=False,
            maxSize=400,
            radiusPercent=100,
            spin=True,
            fps=15,
            scale=480,
            seconds=8,
            q=95,
            spinSeconds=8,
            spinFps=15,
        )
        uploadId = this._state.userClientId
        up = this.uploadAttachment(path, uploadId, ThreadType.USER)
        fileUrl = up.get("fileUrl") if up else None

        try:
            k = filetype.guess(open(path, "rb").read(2048))
            width, height = GetMediaWh(k, filePath=path)
        except:
            width, height = 512, 512

        zaloStk = None
        if fileUrl:
            zaloStk = fileUrl + f"?{this.userName(this.uid).replace(' ', '-')}.zaloStk"

        return fileUrl, zaloStk, int(width or 512), int(height or 512)
    finally:
        try:
            os.remove(path)
        except:
            pass

def UploadVoice(this, song, threadId, type):
    path = download(song)
    if not path:
        return None
    try:
        up = this.uploadAttachment(path, threadId, type)
        return up.get("fileUrl") if up else None
    finally:
        try:
            os.remove(path)
        except:
            pass

def HandleSoundCloudSend(this, data, song, threadId, type):
    s = ReadServices(this.uid)
    spinOn = threadId in (s.get("soundcloudSpinDisk") or [])
    cache = GetSongCache(this, song)

    if not cache["cardHd"]:
        cache["cardHd"] = UploadSongCard(this, song, threadId, type, "sc")

    if spinOn and song.get("cover") and (not cache["stickerFileUrl"] or not cache["stickerZaloStk"]):
        cache["stickerFileUrl"], cache["stickerZaloStk"], cache["stickerW"], cache["stickerH"] = UploadSpinSticker(this, song.get("cover"))

    if not cache["voiceUrl"]:
        cache["voiceUrl"] = UploadVoice(this, song, threadId, type)

    if not cache["voiceUrl"]:
        this.sendMWarning("Upload voice failed", None, threadId, type)
        return

    if this.MediaCache:
        this.MediaCache.set(
            Platf,
            cache["sid"],
            {
                "title": song.get("title"),
                "artist": song.get("artist"),
                "cardHd": cache["cardHd"],
                "stickerFileUrl": cache["stickerFileUrl"],
                "stickerZaloStk": cache["stickerZaloStk"],
                "stickerW": cache["stickerW"],
                "stickerH": cache["stickerH"],
            },
            cache["voiceUrl"],
        )

    this.sendReaction(data, "", threadId, type, -1)

    if cache["cardHd"]:
        this.sendImage(
            imageUrl=cache["cardHd"],
            message=Message(text=""),
            threadId=threadId,
            type=type,
            width=1600,
            height=600
        )

    if spinOn and cache["stickerZaloStk"]:
        this.sendCustomSticker(
            staticImgUrl=cache["stickerZaloStk"],
            animationImgUrl=cache["stickerZaloStk"],
            threadId=threadId,
            type=type,
            width=cache["stickerW"],
            height=cache["stickerH"],
            ttl=3600000,
            ai=False,
        )

    this.sendVoice(cache["voiceUrl"], threadId, type)
    this.sendReaction(data, "/-ok", threadId, type, 100000000)

def SoundCloudSelect(this, data, userId, threadId, type, n):
    st = getattr(this, "soundcloudStates", {}).get(userId)
    if not st or str(st.get("threadId")) != str(threadId):
        return

    if time.time() - st["time"] > Timeout:
        this.soundcloudStates.pop(userId, None)
        this.sendMWarning("Selection expired", userId, threadId, type)
        return

    songs = st.get("songs") or []
    if n == 0:
        this.soundcloudStates.pop(userId, None)
        return
    if n < 1 or n > len(songs):
        return

    key = st.get("msgId")
    if hasattr(this, "_soundcloudCooldown") and key:
        this._soundcloudCooldown[key] = False

    song = songs[n - 1]
    selfState = this.soundcloudStates.pop(userId, None)

    cache = GetSongCache(this, song)
    waitMsg = None

    if not cache["voiceUrl"]:
        waitMsg = this.sendMCustom("WAITING", "y", "Wait, im hooking..!", userId, threadId, type)

    this.sendReaction(data, "🕑", threadId, type, 1000000023)

    def Run():
        try:
            HandleSoundCloudSend(this, data, song, threadId, type)
        finally:
            if waitMsg:
                try:
                    this.deleteMessage(waitMsg.msgId, this.uid, waitMsg.clientId, threadId)
                except:
                    pass

    threading.Thread(target=Run, daemon=True).start()

def ParseSoundCloudArgs(this, text):
    return ParseCommandArgs(this, text, "soundcloud")

def SoundCloudCommand(this, message, data, userId, threadId, type):
    if not hasattr(this, "soundcloudStates"):
        this.soundcloudStates = {}
    EnsureMediaCache(this)

    def SetSpinDisk(enabled):
        ToggleSpinDisk(this, threadId, userId, type, "soundcloudSpinDisk", enabled)

    arg = ParseSoundCloudArgs(this, getattr(message, "text", message))
    if not arg:
        return this.sendMWarning(
            f"use {this.prefix}{this.rawCommand} with a keyword to search your Soundcloud songs..!",
            userId,
            threadId,
            type,
        )

    low = arg.lower()
    if low.startswith("spindisk"):
        parts = low.split()
        if len(parts) == 1:
            return SetSpinDisk(None)
        if parts[1] == "on":
            return SetSpinDisk(True)
        if parts[1] == "off":
            return SetSpinDisk(False)
        return

    songs = SearchSong(arg)
    if not songs:
        return this.sendMWarning("No result", userId, threadId, type)

    imgPath = DrawSongsListCard(
        [
            {
                "title": song.get("title", "Unknown"),
                "artist": song.get("artist", "Unknown"),
                "duration": Fmt(song.get("duration")),
                "cover": song.get("cover")
            }
            for song in songs
        ],
        f"assets/cache/sc_list_{userId}_{int(time.time() * 1000)}.png",
        Title="Kết quả tìm kiếm",
        SubTitle="Chọn số để phát bài",
        Source="SoundCloud",
    )

    width, height = W, H
    try:
        im = Image.open(imgPath)
        width, height = im.size
        im.close()
    except:
        pass

    try:
        up = this.uploadImage(imgPath, threadId, type)
        hd = up.get("hdUrl") if up else None
    finally:
        try:
            os.remove(imgPath)
        except:
            pass

    msg = None
    if hd:
        msg = this.sendImage(
            imageUrl=hd,
            message=Message(text=""),
            threadId=threadId,
            type=type,
            width=int(width),
            height=int(height)
        )

    this.soundcloudStates[userId] = {
        "songs": songs,
        "time": time.time(),
        "msgId": getattr(msg, "msgId", None),
        "cliMsgId": getattr(msg, "clientId", None),
        "threadId": threadId,
        "typeGr": type,
    }

    StartSelectionCooldown(this, "_soundcloudCooldown", msg, threadId, type, Timeout)

def SoundCloudStrip(message, data):
    return StripSelectionText(message, data)

def SoundcloudReply(this, message, data, userId, threadId, type):
    st = getattr(this, "soundcloudStates", {}).get(userId)
    if not st or str(st.get("threadId")) != str(threadId):
        return

    raw = message.text if isinstance(message, Message) else str(message or "")
    raw = raw.strip()

    prefix = str(getattr(this, "prefix", "") or "")
    if prefix and raw.startswith(prefix):
        return

    text = SoundCloudStrip(message, data)
    if not text or not text.isdigit():
        return

    msgId = st.get("msgId")
    cliMsgId = st.get("cliMsgId")

    SoundCloudSelect(this, data, userId, threadId, type, int(text))

    if msgId and cliMsgId:
        try:
            this.deleteMessage(msgId, this.uid, cliMsgId, threadId)
        except:
            pass

def InitTimeoutSoundCloud(this, interval=1):
    InitSelectionTimeout(this, "soundcloudStates", interval=interval, timeout=Timeout)

def SoundcloudAutosend(this, threadId, type, contentText="", options=None):
    options = options if isinstance(options, dict) else {}
    keywords = options.get("Keywords") or options.get("keywords") or ["B Ray", "25", "Rap Viet", "Vpop Chill"]
    keywords = [str(x).strip() for x in keywords if str(x).strip()]
    if not keywords:
        keywords = ["B Ray", "25"]

    query = random.choice(keywords)
    songs = SearchSong(query, limit=20) or []
    songs = [song for song in songs if isinstance(song, dict) and song.get("id") and song.get("link")]
    if not songs:
        logger.errorMeta(f"Soundcloud autosend no song by query: {query}")
        return False

    song = random.choice(songs)
    cache = GetSongCache(this, song)

    if not cache["cardHd"]:
        try:
            cache["cardHd"] = UploadSongCard(this, song, threadId, type, "sc_auto")
        except Exception as e:
            logger.errorMeta(f"Soundcloud autosend upload card failed: {e}")

    if not cache["voiceUrl"]:
        cache["voiceUrl"] = UploadVoice(this, song, threadId, type)

    if not cache["voiceUrl"]:
        logger.errorMeta(f"Soundcloud autosend upload voice failed: {cache['sid']}")
        return False

    if this.MediaCache:
        this.MediaCache.set(
            Platf,
            cache["sid"],
            {
                "title": song.get("title"),
                "artist": song.get("artist"),
                "cardHd": cache["cardHd"],
            },
            cache["voiceUrl"],
        )

    this.sendVoice(cache["voiceUrl"], threadId, type)
    timeno = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).strftime("%H:%M")
    if cache["cardHd"]:
        this.sendImage(
            imageUrl=cache["cardHd"],
            message=Message(text=f"{timeno}\n\n{contentText}"),
            threadId=threadId,
            type=type,
            width=1600,
            height=600
        )

    return True

dependencies = {
    "name": "soundcloud",
    "permission": 0,
    "cooldown": 5,
    "description": "Songs on SoundCloud",
    "main": SoundCloudCommand,
}
