from app.library.packages import *
from functions.services.init.permission import *

def SafeStr(v):
    if v is None:
        return None
    s = str(v)
    return s if s != "" else None

def SafeInt(v, d=None):
    try:
        return int(v)
    except:
        return d

def _RowToMeta(row):
    if not row:
        return None
    fileUrl, metaRaw, tsMs = row[0], row[1], row[2]
    meta = {}
    if metaRaw:
        try:
            meta = json.loads(metaRaw) or {}
        except:
            meta = {}
    meta["fileUrl"] = fileUrl
    meta["timestamp"] = SafeInt(tsMs)
    return meta

class MediaCache:
    def __init__(this, owner=None):
        this.owner = owner
        this.eng = getattr(owner, "MongoWorker", None) if owner is not None else None

    def get(this, platform, sid):
        if not this.eng:
            return None
        try:
            m = this.eng.mediaMongo.Get(SafeStr(platform), SafeStr(sid))
            if not m:
                return None
            ts = m.get("timestamp", None)
            if ts is None:
                ts = m.get("ts_ms", None)
            m["timestamp"] = SafeInt(ts)
            return m
        except:
            return None

    def set(this, platform, sid, meta, fileUrl):
        if not this.eng:
            return False
        try:
            ok = this.eng.mediaMongo.Write(
                str(platform),
                str(sid),
                "" if fileUrl is None else str(fileUrl),
                meta=meta or {},
                ts_ms=int(time.time() * 1000),
            )
            try:
                this.eng.Flush(1.5)
            except:
                pass
            return bool(ok)
        except:
            return False

    def remove(this, platform, sid):
        if not this.eng:
            return False
        try:
            ok = this.eng.mediaMongo.Remove(SafeStr(platform), SafeStr(sid))
            try:
                this.eng.Flush(1.5)
            except:
                pass
            return bool(ok)
        except:
            return False

    def isAlive(this, url, timeout=5):
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=True)
            return r.status_code == 200
        except:
            return False

from src.command.api.music.audiomack import AudiomackReply
from src.command.api.music.soundcloud import SoundcloudReply
from src.command.api.music.zingmp3 import ZingReply
from src.bot.command.menuBot import MenuReply
from src.command.api.music.spotify import SpotifyReply
from src.command.api.music.nhaccuatui import NhacCuaTuiReply
from src.command.api.music.mixcloud import MixcloudReply
from src.command.api.music.youtubemusic import YouTubeMusicReply
from src.bot.manager.groupModify import GroupModifyReply
from src.command.api.browser.tikwm import TikTokReply
from src.events.joinGroup import approveJoin

class Listen:
    def listenReply(this, message, data, userId, threadId, type):
        if not hasattr(this, "MediaCache"):
            this.MediaCache = MediaCache(owner=this)
        AudiomackReply(this, message, data, userId, threadId, type)
        approveJoin(this, message, data, userId, threadId, type)
        SoundcloudReply(this, message, data, userId, threadId, type)
        SpotifyReply(this, message, data, userId, threadId, type)
        ZingReply(this, message, data, userId, threadId, type)
        MenuReply(this, message, data, userId, threadId, type)
        NhacCuaTuiReply(this, message, data, userId, threadId, type)
        MixcloudReply(this, message, data, userId, threadId, type)
        YouTubeMusicReply(this, message, data, userId, threadId, type)
        GroupModifyReply(this, message, data, userId, threadId, type)
        TikTokReply(this, message, data, userId, threadId, type)
