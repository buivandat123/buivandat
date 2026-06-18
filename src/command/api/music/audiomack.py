from functions.services.hook.music_hook.audiomackApi import *
from functions.engine.data.data import ReadServices, WriteService
from functions.services.artistcore.searchSongs import DrawSongsListCard, W, H
from functions.services.artistcore.songsCard import draw_song_card
from functions.engine.data.mediaEngine import MediaCache
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

import os, time, threading, asyncio
from PIL import Image

Platf = "audiomack"
Timeout = 120

def Fmt(t):
    return FmtDuration(t)

def HandleAudiomackSend(this, data, song, threadId, type):
    EnsureMediaCache(this)

    def CacheGet(cache, k, d=None):
        return SharedCacheGet(cache, k, d)

    def IsAlive(url):
        return SharedIsAlive(this, url)

    sid = str(song.get("id") or "")
    cache = this.MediaCache.get(Platf, sid) or {}

    voiceUrl = CacheGet(cache, "fileUrl")
    cardHd = CacheGet(cache, "cardHd")

    if voiceUrl and not IsAlive(voiceUrl):
        voiceUrl = None
    if cardHd and not IsAlive(cardHd):
        cardHd = None

    if not cardHd:
        os.makedirs("assets/cache", exist_ok=True)
        imgPath = f"assets/cache/am_{sid}.png"
        try:
            draw_song_card(
                {
                    "title": song.get("title", "Unknown"),
                    "artist": song.get("artist", "Unknown"),
                    "duration": Fmt(song.get("duration")),
                    "cover": song.get("thumb"),
                    "source": "Audiomack", "sourceIcon": "audiomackIcon.png"
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
                    "source": "Audiomack", "sourceIcon": "audiomackIcon.png"
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
        path = download(song)
        if not path:
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
        {"title": song.get("title"), "artist": song.get("artist"), "cardHd": cardHd},
        voiceUrl,
    )

    this.sendReaction(data, "", threadId, type, -1)
    if cardHd:
        this.sendImage(imageUrl=cardHd, message=Message(text=""), threadId=threadId, type=type, width=1600, height=600)
    
    this.sendVoice(voiceUrl, threadId, type)
    this.sendReaction(data, "/-ok", threadId, type, 100000000)

def AudiomackSelect(this, data, userId, threadId, type, n):
    st = getattr(this, "audiomackStates", {}).get(userId)
    if not st:
        return
    EnsureMediaCache(this)

    if time.time() - st["time"] > Timeout:
        getattr(this, "audiomackStates", {}).pop(userId, None)
        this.sendMWarning("Selection expired", userId, threadId, type)
        return

    songs = st.get("songs") or []
    if n == 0:
        getattr(this, "audiomackStates", {}).pop(userId, None)
        return
    if n < 1 or n > len(songs):
        return

    key = st.get("msgId")
    if hasattr(this, "_audiomackCooldown") and key:
        this._audiomackCooldown[key] = False

    song = songs[n - 1]
    getattr(this, "audiomackStates", {}).pop(userId, None)

    def CacheGet(cache, k, d=None):
        return SharedCacheGet(cache, k, d)

    def IsAlive(url):
        return SharedIsAlive(this, url)

    sid = str(song.get("id") or "")
    cache = this.MediaCache.get(Platf, sid) or {}
    cachedVoice = CacheGet(cache, "fileUrl")
    cachedOk = IsAlive(cachedVoice)

    waitMsg = None
    if not cachedOk:
        waitMsg = this.sendMCustom("WAITING", "y", "Wait, im hooking..!", userId, threadId, type)

    this.sendReaction(data, "🕑", threadId, type, 1000000023)

    def Run():
        try:
            HandleAudiomackSend(this, data, song, threadId, type)
        finally:
            if waitMsg:
                try:
                    this.deleteMessage(waitMsg.msgId, this.uid, waitMsg.clientId, threadId)
                except:
                    pass

    threading.Thread(target=Run, daemon=True).start()

def _ParseAudiomackArgs(this, text):
    return ParseCommandArgs(this, text, "audiomack")

def AudiomackCommand(this, message, data, userId, threadId, type):
    if not hasattr(this, "audiomackStates"):
        this.audiomackStates = {}
    EnsureMediaCache(this)

    def SetSpinDisk(enabled):
        ToggleSpinDisk(this, threadId, userId, type, "audiomackSpinDisk", enabled)

    arg = _ParseAudiomackArgs(this, getattr(message, "text", message))
    if not arg:
        return this.sendMWarning(
            f"use {this.prefix}{this.rawCommand} with a keyword to search your Audiomack songs..!",
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
        [{"title": s.get("title", "Unknown"), "artist": s.get("artist", "Unknown"), "duration": Fmt(s.get("duration")), "cover": s.get("thumb")} for s in songs],
        f"assets/cache/am_list_{userId}_{int(time.time()*1000)}.png",
        Title="Kết quả tìm kiếm",
        SubTitle="Chọn số để phát bài",
        Source="Audiomack",
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

    this.audiomackStates[userId] = {
        "songs": songs,
        "time": time.time(),
        "msgId": getattr(msg, "msgId", None),
        "cliMsgId": getattr(msg, "clientId", None),
        "threadId": threadId,
        "typeGr": type,
    }

    StartSelectionCooldown(this, "_audiomackCooldown", msg, threadId, type, Timeout)

def AudiomackStrip(message, data):
    return StripSelectionText(message, data)

def AudiomackReply(this, message, data, userId, threadId, type):
    st = getattr(this, "audiomackStates", {}).get(userId)
    if not st:
        return
    if str(st.get("threadId")) != str(threadId):
        return

    raw = ""
    if isinstance(message, Message):
        raw = message.text or ""
    else:
        raw = str(message or "")
    raw = raw.strip()

    p = str(getattr(this, "prefix", "") or "")
    if p and raw.startswith(p):
        return

    txt = AudiomackStrip(message, data)
    if not txt or not txt.isdigit():
        return

    msgId = st.get("msgId")
    cliMsgId = st.get("cliMsgId")

    AudiomackSelect(this, data, userId, threadId, type, int(txt))

    if msgId and cliMsgId:
        try:
            this.deleteMessage(msgId, this.uid, cliMsgId, threadId)
        except:
            pass

def InitTimeoutAudiomack(this, interval=1):
    InitSelectionTimeout(this, "audiomackStates", interval=interval, timeout=Timeout)

dependencies = {
    "name": "audiomack",
    "permission": 0,
    "cooldown": 5,
    "description": "Songs on Audiomack",
    "main": AudiomackCommand,
}
