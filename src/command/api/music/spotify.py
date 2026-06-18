from functions.services.hook.music_hook.spotifyApi import *
from functions.engine.data.data import ReadServices, WriteService
from functions.services.artistcore.searchSongs import DrawSongsListCard, W, H
from functions.services.artistcore.songsCard import draw_song_card
from functions.engine.data.mediaEngine import MediaCache
from src.command.chatBot.special.sticker import CreateStickerUrl, MaxStickerSize, GetMediaWh
from src.command.api.music._shared import (
    FmtDuration,
    EnsureMediaCache,
    CacheGet as SharedCacheGet,
    IsAlive as SharedIsAlive,
    ParseCommandArgs,
    StripSelectionText,
    ToggleSpinDisk,
    StartSelectionCooldown,
    InitSelectionTimeout,
)

Platf = "spotify"
Timeout = 120

def _FriendlySpotifyErrorMessage(err):
    text = str(err or "")
    low = text.lower()
    if "active premium subscription required" in low or "status=403" in low:
        return "Spotify API đang bị chặn do app owner chưa có Premium, thử lại sau vài giờ hoặc đổi nguồn nhạc khác."
    if "spotifytokenerror" in low or "spotifytokeninvalid" in low:
        return "Spotify token không hợp lệ hoặc đã hết hạn, vui lòng kiểm tra Spotify Client."
    return "Spotify đang lỗi tạm thời, vui lòng thử lại sau."

def Fmt(t):
    return FmtDuration(t)

def _CacheGet(cache, k, d=None):
    return SharedCacheGet(cache, k, d)

def _IsAlive(this, url):
    return SharedIsAlive(this, url)

def _PickNewestFile(dirPath, exts=None, minSize=1024):
    try:
        exts = set([e.lower().lstrip(".") for e in (exts or ["mp3", "m4a", "webm", "ogg", "wav"])])
        bestP = None
        bestT = 0
        for root, _, files in os.walk(dirPath):
            for fn in files:
                ext = (fn.rsplit(".", 1)[-1] if "." in fn else "").lower()
                if ext not in exts:
                    continue
                p = os.path.join(root, fn)
                try:
                    if os.path.getsize(p) < minSize:
                        continue
                    mt = os.path.getmtime(p)
                    if mt > bestT:
                        bestT = mt
                        bestP = p
                except:
                    pass
        return bestP
    except:
        return None

def _DownloadSpotify(song):
    try:
        p = download(song)
        if p and os.path.exists(p) and os.path.getsize(p) > 0:
            return p
    except:
        pass

    try:
        link = (song or {}).get("link")
        if not link:
            return None
        os.makedirs("assets/cache", exist_ok=True)
        before = time.time()
        try:
            subprocess.run(["aio-down", link], capture_output=True, text=True, check=False)
        except:
            return None
        p = _PickNewestFile("assets/cache")
        if not p:
            return None
        try:
            if os.path.getmtime(p) < before - 2:
                return None
        except:
            pass
        return p
    except:
        return None

def HandleSpotifySend(this, data, song, threadId, type):
    EnsureMediaCache(this)

    s = ReadServices(this.uid)
    spinOn = threadId in (s.get("spotifySpinDisk") or [])

    sid = str(song.get("id") or "")
    if not sid:
        this.sendMWarning("Invalid song id", None, threadId, type)
        return

    coverUrl = song.get("cover")
    cache = this.MediaCache.get(Platf, sid) or {}

    voiceUrl = _CacheGet(cache, "fileUrl")
    cardHd = _CacheGet(cache, "cardHd")
    stickerFileUrl = _CacheGet(cache, "stickerFileUrl") or _CacheGet(cache, "stickerUrl")
    stickerZaloStk = _CacheGet(cache, "stickerZaloStk")
    stickerW = int(_CacheGet(cache, "stickerW", 512) or 512)
    stickerH = int(_CacheGet(cache, "stickerH", 512) or 512)

    if voiceUrl and not _IsAlive(this, voiceUrl):
        voiceUrl = None
    if cardHd and not _IsAlive(this, cardHd):
        cardHd = None
    if stickerFileUrl and not _IsAlive(this, stickerFileUrl):
        stickerFileUrl = None
        stickerZaloStk = None
    if stickerZaloStk and not _IsAlive(this, stickerZaloStk.split("?", 1)[0]):
        stickerZaloStk = None

    if not cardHd:
        os.makedirs("assets/cache", exist_ok=True)
        imgPath = f"assets/cache/sp_{sid}.png"
        try:
            draw_song_card(
                {
                    "title": song.get("title", "Unknown"),
                    "artist": song.get("artist", "Unknown"),
                    "duration": Fmt(song.get("duration")),
                    "cover": coverUrl,
                    "source": "Spotify", "sourceIcon": "spotifyFlatIcon.png"
                },
                imgPath,
            )
        except:
            draw_song_card(
                {
                    "title": song.get("title", "Unknown"),
                    "artist": song.get("artist", "Unknown"),
                    "duration": Fmt(song.get("duration")),
                    "cover": None,
                    "source": "Spotify", "sourceIcon": "spotifyFlatIcon.png"
                },
                imgPath,
            )
        up = this.uploadImage(imgPath, threadId, type)
        cardHd = up.get("hdUrl") if up else None
        try:
            os.remove(imgPath)
        except:
            pass

    if spinOn and coverUrl and (not stickerFileUrl or not stickerZaloStk):
        os.makedirs("assets/cache", exist_ok=True)
        outPath = f"assets/cache/sp_spin_{int(time.time()*1000)}.webp"
        CreateStickerUrl(
            coverUrl,
            outPath,
            xp=False,
            maxSize=MaxStickerSize,
            radiusPercent=100,
            spin=True,
            fps=30,
            scale=480,
            seconds=6,
            q=95,
            spinSeconds=6,
            spinFps=60,
        )
        uploadId = this._state.userClientId
        r = this.uploadAttachment(outPath, uploadId, ThreadType.USER)
        stickerFileUrl = r.get("fileUrl") if r else None
        try:
            k = filetype.guess(open(outPath, "rb").read(2048))
            stickerW, stickerH = GetMediaWh(k, filePath=outPath)
        except:
            stickerW, stickerH = 512, 512
        try:
            os.remove(outPath)
        except:
            pass
        if stickerFileUrl:
            stickerZaloStk = stickerFileUrl + f"?{this.userName(this.uid).replace(' ', '-')}.zaloStk"

    if not voiceUrl:
        path = _DownloadSpotify(song)
        if not path:
            this.sendMWarning("Failed download", None, threadId, type)
            return
        lowp = str(path).lower()
        if lowp.endswith((".webp", ".png", ".jpg", ".jpeg")):
            this.sendMWarning("Failed download", None, threadId, type)
            return

        up = this.uploadAttachment(path, threadId, type)
        voiceUrl = up.get("fileUrl") if up else None
        try:
            os.remove(path)
        except:
            pass

    if not voiceUrl:
        this.sendMWarning("Upload voice failed", None, threadId, type)
        return

    this.MediaCache.set(
        Platf,
        sid,
        {
            "title": song.get("title"),
            "artist": song.get("artist"),
            "cardHd": cardHd,
            "stickerFileUrl": stickerFileUrl,
            "stickerZaloStk": stickerZaloStk,
            "stickerW": int(stickerW or 512),
            "stickerH": int(stickerH or 512),
        },
        voiceUrl,
    )

    this.sendReaction(data, "", threadId, type, -1)
    if cardHd:
        this.sendImage(imageUrl=cardHd, message=Message(text=""), threadId=threadId, type=type, width=1600, height=600)
    if spinOn and stickerZaloStk:
        this.sendCustomSticker(
            staticImgUrl=stickerZaloStk,
            animationImgUrl=stickerZaloStk,
            threadId=threadId,
            type=type,
            width=int(stickerW or 512),
            height=int(stickerH or 512),
            ttl=3600000,
            ai=False,
        )
    
    this.sendVoice(voiceUrl, threadId, type)
    this.sendReaction(data, "/-ok", threadId, type, 100000000)

def _ParseSpotifyArgs(this, text):
    return ParseCommandArgs(this, text, "spotify")

def SpotifySelect(this, data, userId, threadId, type, n):
    st = getattr(this, "spotifyStates", {}).get(userId)
    if not st:
        return
    if str(st.get("threadId")) != str(threadId):
        return

    if time.time() - st["time"] > Timeout:
        getattr(this, "spotifyStates", {}).pop(userId, None)
        this.sendMWarning("Selection expired", userId, threadId, type)
        return

    songs = st.get("songs") or []
    if n == 0:
        getattr(this, "spotifyStates", {}).pop(userId, None)
        return
    if n < 1 or n > len(songs):
        return

    key = st.get("msgId")
    if hasattr(this, "_spotifyCooldown") and key:
        this._spotifyCooldown[key] = False

    song = songs[n - 1]
    getattr(this, "spotifyStates", {}).pop(userId, None)

    sid = str(song.get("id") or "")
    cache = this.MediaCache.get(Platf, sid) or {}
    cachedVoice = _CacheGet(cache, "fileUrl")
    cachedOk = _IsAlive(this, cachedVoice)

    waitMsg = None
    if not cachedOk:
        waitMsg = this.sendMCustom("WAITING", "y", "Wait, im hooking..!", userId, threadId, type)

    this.sendReaction(data, "🕑", threadId, type, 1000000023)

    def Run():
        try:
            HandleSpotifySend(this, data, song, threadId, type)
        finally:
            if waitMsg:
                try:
                    this.deleteMessage(waitMsg.msgId, this.uid, waitMsg.clientId, threadId)
                except:
                    pass

    threading.Thread(target=Run, daemon=True).start()

def SpotifyCommand(this, message, data, userId, threadId, type):
    if not hasattr(this, "spotifyStates"):
        this.spotifyStates = {}
    EnsureMediaCache(this)

    def SetSpinDisk(enabled):
        ToggleSpinDisk(this, threadId, userId, type, "spotifySpinDisk", enabled)

    arg = _ParseSpotifyArgs(this, getattr(message, "text", message))
    if not arg:
        return this.sendMWarning(f"use {this.prefix}{this.rawCommand} with a keyword or link to search and download Spotify songs", userId, threadId, type)

    low = arg.lower()
    if low.startswith("spindisk"):
        p = low.split()
        if len(p) == 1:
            return SetSpinDisk(None)
        if p[1] == "on":
            return SetSpinDisk(True)
        if p[1] == "off":
            return SetSpinDisk(False)
        return

    if "open.spotify.com/track/" in low or low.startswith("spotify:track:"):
        try:
            song = resolve(arg, market="VN")
        except Exception as e:
            logger.errorMeta(f"spotify resolve failed: {e}")
            return this.sendMWarning(_FriendlySpotifyErrorMessage(e), userId, threadId, type)
        if not song:
            return this.sendMWarning("No result", userId, threadId, type)

        sid = str(song.get("id") or "")
        cache = this.MediaCache.get(Platf, sid) or {}
        cachedVoice = _CacheGet(cache, "fileUrl")
        cachedOk = _IsAlive(this, cachedVoice)

        waitMsg = None
        if not cachedOk:
            waitMsg = this.sendMCustom("WAITING", "y", "Wait, im hooking..!", userId, threadId, type)

        this.sendReaction(data, "🕑", threadId, type, 1000000023)

        def RunLink():
            try:
                HandleSpotifySend(this, data, song, threadId, type)
            finally:
                if waitMsg:
                    try:
                        this.deleteMessage(waitMsg.msgId, this.uid, waitMsg.clientId, threadId)
                    except:
                        pass

        threading.Thread(target=RunLink, daemon=True).start()
        return

    try:
        songs = SearchSong(arg, limit=10, market="VN")
    except Exception as e:
        logger.errorMeta(f"spotify search failed: {e}")
        return this.sendMWarning(_FriendlySpotifyErrorMessage(e), userId, threadId, type)
    if not songs:
        return this.sendMWarning("No result", userId, threadId, type)

    imgPath = DrawSongsListCard(
        [{"title": s.get("title", "Unknown"), "artist": s.get("artist", "Unknown"), "duration": Fmt(s.get("duration")), "cover": s.get("cover")} for s in songs],
        f"assets/cache/sp_list_{userId}_{int(time.time()*1000)}.png",
        Title="Kết quả tìm kiếm",
        SubTitle="Chọn số để phát bài",
        Source="Spotify",
    )

    w = W
    h = H
    try:
        im = Image.open(imgPath)
        w, h = im.size
        im.close()
    except:
        pass

    up = this.uploadImage(imgPath, threadId, type)
    hd = up.get("hdUrl") if up else None
    try:
        os.remove(imgPath)
    except:
        pass

    msg = None
    if hd:
        msg = this.sendImage(imageUrl=hd, message=Message(text=""), threadId=threadId, type=type, width=int(w), height=int(h))

    this.spotifyStates[userId] = {
        "songs": songs,
        "time": time.time(),
        "msgId": getattr(msg, "msgId", None),
        "cliMsgId": getattr(msg, "clientId", None),
        "threadId": threadId,
        "typeGr": type,
    }

    StartSelectionCooldown(this, "_spotifyCooldown", msg, threadId, type, Timeout)

def SpotifyStrip(message, data):
    return StripSelectionText(message, data)

def SpotifyReply(this, message, data, userId, threadId, type):
    st = getattr(this, "spotifyStates", {}).get(userId)
    if not st:
        return
    if str(st.get("threadId")) != str(threadId):
        return

    raw = message.text if isinstance(message, Message) else str(message or "")
    if not isinstance(raw, str):
        return
    raw = raw.strip()

    p = str(getattr(this, "prefix", "") or "")
    if p and raw.startswith(p):
        return

    txt = SpotifyStrip(message, data)
    if not txt or not txt.isdigit():
        return

    msgId = st.get("msgId")
    cliMsgId = st.get("cliMsgId")

    SpotifySelect(this, data, userId, threadId, type, int(txt))

    if msgId and cliMsgId:
        try:
            this.deleteMessage(msgId, this.uid, cliMsgId, threadId)
        except:
            pass

def InitTimeoutSpotify(this, interval=1):
    InitSelectionTimeout(this, "spotifyStates", interval=interval, timeout=Timeout)

dependencies = {
    "name": "spotify",
    "permission": 0,
    "cooldown": 5,
    "description": "Songs on Spotify",
    "main": SpotifyCommand,
}
