from dto.index import *

YtmCacheDir = "assets/cache"
YtmUserAgent = "Mozilla/5.0"

AUDIO_EXTS = (".mp3", ".m4a", ".opus", ".ogg", ".wav", ".flac", ".aac", ".webm")
BAD_EXTS = (".webp", ".jpg", ".jpeg", ".png")

def _GetFfmpegPath():
    try:
        cfg = databaseReader() or {}
        if isinstance(cfg, dict):
            p = (cfg.get("ffmpegPath") or "").strip()
            return p or None
    except:
        pass
    try:
        with open("assets/config/database-config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        p = (cfg.get("ffmpegPath") or "").strip()
        return p or None
    except:
        return None

def Norm(s):
    return (s or "").strip()

def ToInt(v, d=0):
    try:
        return int(v)
    except:
        return d

def SafeName(s):
    s = Norm(s)
    s = re.sub(r"[\\/:*?\"<>|\n\r\t]+", "_", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:120] if s else "ytm"

def BuildUrl(videoId):
    vid = Norm(videoId)
    return f"https://music.youtube.com/watch?v={vid}" if vid else ""

def _IsSongItem(x):
    return isinstance(x, dict) and bool(Norm(x.get("videoId")))

def _ArtistsToStr(artists):
    if not isinstance(artists, list):
        return ""
    return ", ".join([Norm(a.get("name")) for a in artists if isinstance(a, dict) and Norm(a.get("name"))]).strip()

def _ParseDurSec(dur):
    s = Norm(dur)
    if not s:
        return 0
    if s.isdigit():
        return int(s)
    parts = [p for p in s.split(":") if p.isdigit()]
    if not parts:
        return 0
    parts = [int(p) for p in parts]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]

def SongToSongLite(x):
    vid = Norm(x.get("videoId"))
    title = Norm(x.get("title"))
    artist = _ArtistsToStr(x.get("artists")) or Norm(x.get("artist"))
    albumObj = x.get("album") if isinstance(x.get("album"), dict) else {}
    album = Norm(albumObj.get("name"))
    thumbs = x.get("thumbnails") if isinstance(x.get("thumbnails"), list) else []
    cover = Norm((thumbs[-1] or {}).get("url")) if thumbs else ""
    dur = _ParseDurSec(x.get("duration")) or ToInt(x.get("duration_seconds"), 0)
    return {
        "id": vid or None,
        "title": title or None,
        "link": BuildUrl(vid) or None,
        "artist": artist or None,
        "cover": cover or None,
        "duration": dur,
        "like": 0,
        "listen": 0,
        "comment": 0,
        "explicit": bool(x.get("isExplicit")) if x.get("isExplicit") is not None else None,
        "previewUrl": None,
        "uri": vid or None,
        "isPlayable": None,
        "key": vid or None,
        "album": album or None,
        "videoId": vid or None,
    }

def resolve(videoId):
    vid = Norm(videoId)
    if not vid:
        raise RuntimeError("InvalidYtmVideoId")
    return YTMusic().get_song(vid) or {}

def SearchSong(q, limit=10, pageIndex=1, correct=False):
    qq = Norm(q)
    if not qq:
        return []
    lim = max(1, ToInt(limit, 10))
    page = max(1, ToInt(pageIndex, 1))
    need = lim * page
    yt = YTMusic()
    res = yt.search(qq, filter="songs", limit=need) or []
    items = [x for x in res if _IsSongItem(x)]
    if not items:
        res = yt.search(qq, limit=need) or []
        items = [x for x in res if _IsSongItem(x)]
    start = (page - 1) * lim
    return [SongToSongLite(x) for x in items[start:start + lim]]

def _FindNewestAudio(outDir, prefix):
    try:
        outDir = os.path.abspath(outDir)
        pref = (prefix or "").lower()
        best, bestMt = None, -1
        for fn in os.listdir(outDir):
            lp = fn.lower()
            if not lp.startswith(pref):
                continue
            if lp.endswith((".part", ".ytdl", ".tmp")):
                continue
            if lp.endswith(BAD_EXTS):
                continue
            if not lp.endswith(AUDIO_EXTS):
                continue
            fp = os.path.join(outDir, fn)
            if not os.path.isfile(fp):
                continue
            mt = os.path.getmtime(fp)
            if mt > bestMt:
                bestMt, best = mt, fp
        return best
    except:
        return None

def _RunYtDlp(url, outDir, audioFormat="mp3", keepVideo=False, title="", artist=""):
    os.makedirs(outDir, exist_ok=True)
    base = SafeName(title) if title else "ytm"
    art = SafeName(artist)
    stem = f"ytm_{base}-{art}_{int(time.time()*1000)}" if art else f"ytm_{base}_{int(time.time()*1000)}"
    tpl = os.path.join(outDir, stem + ".%(ext)s")

    cmd = ["yt-dlp", "--no-playlist", "--user-agent", YtmUserAgent, "-o", tpl]
    ff = _GetFfmpegPath()
    if ff:
        cmd += ["--ffmpeg-location", ff]

    if keepVideo:
        cmd.append(url)
    else:
        cmd += ["-x", "--audio-quality", "0", "--add-metadata", "--embed-thumbnail"]
        if audioFormat and audioFormat != "best":
            cmd += ["--audio-format", audioFormat]
        cmd.append(url)

    subprocess.run(cmd, capture_output=True, text=True)

    if not keepVideo and audioFormat and audioFormat != "best":
        want = "." + audioFormat.lower().lstrip(".")
        fp = os.path.join(outDir, stem + want)
        if os.path.exists(fp) and os.path.isfile(fp):
            return fp

    newest = _FindNewestAudio(outDir, stem.lower())
    return newest if newest and os.path.exists(newest) else None

def download(song, outDir=YtmCacheDir, audioFormat="mp3", keepVideo=False):
    s = song or {}
    vid = Norm(s.get("videoId") or s.get("id") or s.get("key"))
    if not vid:
        return None
    url = BuildUrl(vid)
    if not url:
        return None

    title = Norm(s.get("title") or s.get("name"))
    artist = Norm(s.get("artist") or s.get("artistName"))

    p = _RunYtDlp(url, outDir, audioFormat=audioFormat, keepVideo=keepVideo, title=title, artist=artist)
    if not p:
        return None
    lp = str(p).lower()
    if lp.endswith(BAD_EXTS):
        return None
    return p