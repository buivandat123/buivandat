from functions.services.hook.music_hook.nhaccuatuiApi import *
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

Platf = "nhaccuatui"
Timeout = 120

def Fmt(t):
    return FmtDuration(t)

def HandleNhacCuaTuiSend(this, data, song, threadId, type):
    EnsureMediaCache(this)

    def CacheGet(cache, k, d=None):
        return SharedCacheGet(cache, k, d)

    def IsAlive(url):
        return SharedIsAlive(this, url)

    s = ReadServices(this.uid)
    spinOn = threadId in (s.get("nhaccuatuiSpinDisk") or [])

    sid = str(song.get("id") or song.get("key") or song.get("code") or "")
    if not sid:
        sid = str(int(time.time() * 1000))

    coverUrl = song.get("cover") or song.get("thumbnail") or song.get("thumb")
    cache = this.MediaCache.get(Platf, sid) or {}

    voiceUrl = CacheGet(cache, "fileUrl")
    cardHd = CacheGet(cache, "cardHd")
    stickerFileUrl = CacheGet(cache, "stickerFileUrl") or CacheGet(cache, "stickerUrl")
    stickerZaloStk = CacheGet(cache, "stickerZaloStk")
    stickerW = int(CacheGet(cache, "stickerW", 512) or 512)
    stickerH = int(CacheGet(cache, "stickerH", 512) or 512)

    if voiceUrl and not IsAlive(voiceUrl):
        voiceUrl = None
    if cardHd and not IsAlive(cardHd):
        cardHd = None
    if stickerFileUrl and not IsAlive(stickerFileUrl):
        stickerFileUrl = None
        stickerZaloStk = None
    if stickerZaloStk and not IsAlive(stickerZaloStk.split("?", 1)[0]):
        stickerZaloStk = None

    if not cardHd:
        os.makedirs("assets/cache", exist_ok=True)
        imgPath = f"assets/cache/nct_{sid}.png"
        payload = {
            "title": song.get("title", "Unknown"),
            "artist": song.get("artist", "Unknown"),
            "duration": Fmt(song.get("duration")),
            "cover": coverUrl,
            "source": "NhacCuaTui", "sourceIcon": "nhaccuatuiIcon.png"
        }
        try:
            draw_song_card(payload, imgPath)
        except:
            payload["cover"] = None
            draw_song_card(payload, imgPath)

        up = this.uploadImage(imgPath, threadId, type)
        cardHd = up.get("hdUrl") if up else None
        try:
            os.remove(imgPath)
        except:
            pass

    if spinOn and coverUrl and (not stickerFileUrl or not stickerZaloStk):
        os.makedirs("assets/cache", exist_ok=True)
        outPath = f"assets/cache/nct_spin_{int(time.time()*1000)}.webp"
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
        path = download(song)
        if not path:
            this.sendMWarning("Failed download", None, threadId, type)
            return
        up = None
        up = this.uploadAttachment(path, threadId, type)
        voiceUrl = up.get("fileUrl") if up else None
        os.remove(path)
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

def NhacCuaTuiSelect(this, data, userId, threadId, type, n):
    st = getattr(this, "nhaccuatuiStates", {}).get(userId)
    if not st:
        return
    if str(st.get("threadId")) != str(threadId):
        return

    if time.time() - st["time"] > Timeout:
        getattr(this, "nhaccuatuiStates", {}).pop(userId, None)
        this.sendMWarning("Selection expired", userId, threadId, type)
        return

    songs = st.get("songs") or []
    if n == 0:
        getattr(this, "nhaccuatuiStates", {}).pop(userId, None)
        return
    if n < 1 or n > len(songs):
        return

    key = st.get("msgId")
    if hasattr(this, "_nhaccuatuiCooldown") and key:
        this._nhaccuatuiCooldown[key] = False

    song = songs[n - 1]
    getattr(this, "nhaccuatuiStates", {}).pop(userId, None)

    EnsureMediaCache(this)

    def CacheGet(cache, k, d=None):
        return SharedCacheGet(cache, k, d)

    def IsAlive(url):
        return SharedIsAlive(this, url)

    sid = str(song.get("id") or song.get("key") or song.get("code") or "")
    cache = this.MediaCache.get(Platf, sid) or {}
    cachedVoice = CacheGet(cache, "fileUrl")
    cachedOk = IsAlive(cachedVoice)

    waitMsg = None
    if not cachedOk:
        waitMsg = this.sendMCustom("WAITING", "y", "Wait, im hooking..!", userId, threadId, type)

    this.sendReaction(data, "🕑", threadId, type, 1000000023)

    def Run():
        try:
            HandleNhacCuaTuiSend(this, data, song, threadId, type)
        finally:
            if waitMsg:
                try:
                    this.deleteMessage(waitMsg.msgId, this.uid, waitMsg.clientId, threadId)
                except:
                    pass

    threading.Thread(target=Run, daemon=True).start()

def _ParseNhacCuaTuiArgs(this, text):
    return ParseCommandArgs(this, text, "nhaccuatui")

def NhacCuaTuiCommand(this, message, data, userId, threadId, type):
    if not hasattr(this, "nhaccuatuiStates"):
        this.nhaccuatuiStates = {}
    EnsureMediaCache(this)

    def SetSpinDisk(enabled):
        ToggleSpinDisk(this, threadId, userId, type, "nhaccuatuiSpinDisk", enabled)

    arg = _ParseNhacCuaTuiArgs(this, getattr(message, "text", message))
    if not arg:
        return this.sendMWarning(
            f"use {this.prefix}{this.rawCommand} with a keyword to search your Nhaccuatui songs..!",
            userId,
            threadId,
            type,
        )

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

    songs = SearchSong(arg)
    if not songs:
        return this.sendMWarning("No result", userId, threadId, type)

    imgPath = DrawSongsListCard(
        [{"title": s.get("title", "Unknown"), "artist": s.get("artist", "Unknown"), "duration": Fmt(s.get("duration")), "cover": s.get("cover") or s.get("thumbnail") or s.get("thumb")} for s in songs],
        f"assets/cache/nct_list_{userId}_{int(time.time()*1000)}.png",
        Title="Kết quả tìm kiếm",
        SubTitle="Chọn số để phát bài",
        Source="NhacCuaTui",
    )

    w, h = W, H
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

    this.nhaccuatuiStates[userId] = {
        "songs": songs,
        "time": time.time(),
        "msgId": getattr(msg, "msgId", None),
        "cliMsgId": getattr(msg, "clientId", None),
        "threadId": threadId,
        "typeGr": type,
    }

    StartSelectionCooldown(this, "_nhaccuatuiCooldown", msg, threadId, type, Timeout)

def NhacCuaTuiStrip(message, data):
    return StripSelectionText(message, data)

def NhacCuaTuiReply(this, message, data, userId, threadId, type):
    st = getattr(this, "nhaccuatuiStates", {}).get(userId)
    if not st:
        return
    if str(st.get("threadId")) != str(threadId):
        return

    raw = message.text if isinstance(message, Message) else str(message or "")
    raw = str(raw or "").strip()

    p = str(getattr(this, "prefix", "") or "")
    if p and raw.startswith(p):
        return

    txt = NhacCuaTuiStrip(message, data)
    if not txt or not txt.isdigit():
        return

    msgId = st.get("msgId")
    cliMsgId = st.get("cliMsgId")

    NhacCuaTuiSelect(this, data, userId, threadId, type, int(txt))

    if msgId and cliMsgId:
        try:
            this.deleteMessage(msgId, this.uid, cliMsgId, threadId)
        except:
            pass

def InitTimeoutNhacCuaTui(this, interval=1):
    InitSelectionTimeout(this, "nhaccuatuiStates", interval=interval, timeout=Timeout)

dependencies = {
    "name": "nhaccuatui",
    "permission": 0,
    "cooldown": 5,
    "description": "Songs on NhacCuaTui",
    "main": NhacCuaTuiCommand,
}
