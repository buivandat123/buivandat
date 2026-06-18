from dto.index import *

NctApiBase = "https://graph.nhaccuatui.com/api/v1"
SearchSongPath = "/search/song"
DetailSongTpl = "/song/detail/{SongKey}"
TimeoutSec = 15
UserAgent = "Mozilla/5.0"
CacheDir = "assets/cache"
def Norm(s):
    return (s or "").strip()

def NowMs():
    return int(time.time() * 1000)

def ToBoolStr(v):
    return "true" if v else "false"

def H():
    return {"User-Agent": UserAgent, "Accept": "application/json,*/*"}

def Get(path, params=None):
    p = Norm(path)
    if not p:
        raise RuntimeError("NctInvalidPath")
    if not p.startswith("/"):
        p = "/" + p
    r = requests.get(f"{NctApiBase}{p}", params=params or {}, headers=H(), timeout=TimeoutSec)
    if r.status_code != 200:
        raise RuntimeError(f"NctApiError status={r.status_code} body={r.text}")
    return r.json()

def PickByType(items, t, field):
    if not items:
        return ""
    st = str(t)
    for i in items:
        if str(i.get("type")) == st:
            return Norm(i.get(field))
    return ""

def SongToSongLite(x):
    streams = (x or {}).get("streamURL") or []
    key = Norm((x or {}).get("key"))
    title = Norm((x or {}).get("name"))
    artist = Norm((x or {}).get("artistName"))
    link = Norm((x or {}).get("linkShare"))
    image = Norm((x or {}).get("image"))
    duration = int((x or {}).get("duration") or 0)

    return {
        "id": key or None,
        "title": title or None,
        "link": link or None,
        "artist": artist or None,
        "cover": image or None,
        "duration": duration,
        "like": 0,
        "listen": int((x or {}).get("viewed") or 0),
        "comment": 0,
        "explicit": None,
        "previewUrl": PickByType(streams, 128, "stream") or None,
        "uri": key or None,
        "isPlayable": None,

        "key": key or None,
        "image": image or None,
        "stream": {
            "128": PickByType(streams, 128, "stream") or None,
            "320": PickByType(streams, 320, "stream") or None,
            "lossless": PickByType(streams, "lossless", "stream") or None,
        },
        "download": {
            "128": PickByType(streams, 128, "download") or None,
            "320": PickByType(streams, 320, "download") or None,
            "lossless": PickByType(streams, "lossless", "download") or None,
        },
    }

def SongDetailToSong(d):
    streams = (d or {}).get("streamURL") or []
    ql = (d or {}).get("qualityDownload") or []
    provider = (d or {}).get("provider") or {}
    artists = (d or {}).get("artist") or []

    key = Norm((d or {}).get("key"))
    title = Norm((d or {}).get("name"))
    artistName = Norm((d or {}).get("artistName"))
    linkShare = Norm((d or {}).get("linkShare"))
    image = Norm((d or {}).get("image"))
    duration = int((d or {}).get("duration") or 0)

    out = {
        "id": key or None,
        "title": title or None,
        "link": linkShare or None,
        "artist": artistName or None,
        "cover": image or None,
        "duration": duration,
        "like": 0,
        "listen": int((d or {}).get("viewed") or 0),
        "comment": 0,
        "explicit": None,
        "previewUrl": PickByType(streams, 128, "stream") or None,
        "uri": key or None,
        "isPlayable": None,

        "key": key or None,
        "name": title or None,
        "artistName": artistName or None,
        "dateRelease": int((d or {}).get("dateRelease") or 0),
        "viewed": int((d or {}).get("viewed") or 0),
        "genreName": Norm((d or {}).get("genreName")) or None,
        "image": image or None,
        "bgImage": Norm((d or {}).get("bgImage")) or None,

        "provider": {
            "name": Norm(provider.get("name")) or None,
            "image": Norm(provider.get("image")) or None,
            "key": Norm(provider.get("key")) or None,
            "userId": Norm(provider.get("userId")) or None,
        },

        "artists": [{
            "key": Norm(a.get("key")) or None,
            "name": Norm(a.get("name")) or None,
            "image": Norm(a.get("image")) or None,
            "totalFollow": int(a.get("totalFollow") or 0),
        } for a in artists],

        "quality": [{
            "key": Norm(i.get("key")) or None,
            "name": Norm(i.get("name")) or None,
            "value": int(i.get("value") or 0),
            "fileSize": int(i.get("fileSize") or 0),
            "onlyVIP": bool(i.get("onlyVIP") or False),
            "status": int(i.get("status") or 0),
        } for i in ql],

        "stream": {
            "128": PickByType(streams, 128, "stream") or None,
            "320": PickByType(streams, 320, "stream") or None,
            "lossless": PickByType(streams, "lossless", "stream") or None,
        },
        "download": {
            "128": PickByType(streams, 128, "download") or None,
            "320": PickByType(streams, 320, "download") or None,
            "lossless": PickByType(streams, "lossless", "download") or None,
        },

        "flags": (d or {}).get("flags") or [],
        "vipFree": bool((d or {}).get("vipFree") or False),
    }
    return out

def resolve(songKey, isDailyMix=False):
    k = Norm(songKey)
    if not k:
        raise RuntimeError("InvalidNctSongKey")
    j = Get(DetailSongTpl.format(SongKey=k), params={
        "isDailyMix": ToBoolStr(bool(isDailyMix)),
        "key": k,
        "timestamp": NowMs(),
    })
    d = (j or {}).get("data") or {}
    if not d:
        raise RuntimeError("NctSongDetailEmpty")
    return SongDetailToSong(d)

def SearchSong(q, limit=10, pageIndex=1, correct=False):
    qq = Norm(q)
    if not qq:
        return []
    lim = int(limit)
    if lim <= 0:
        lim = 10
    j = Get(SearchSongPath, params={
        "keyword": qq,
        "pageindex": int(pageIndex),
        "pagesize": lim,
        "correct": ToBoolStr(bool(correct)),
        "timestamp": NowMs(),
    })
    songs = ((j or {}).get("data") or {}).get("songs") or []
    return [SongToSongLite(x) for x in songs]

def _SafeName(s):
    s = (s or "").strip()
    s = re.sub(r"[\\/:*?\"<>|\n\r\t]+", "_", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:120] if s else "nct"

def _PickBestUrl(song):
    d = (song or {}).get("download") or {}
    s = (song or {}).get("stream") or {}
    for k in ("lossless", "320", "128"):
        u = (d.get(k) or "").strip()
        if u:
            return u, k
    for k in ("lossless", "320", "128"):
        u = (s.get(k) or "").strip()
        if u:
            return u, k
    u = (song or {}).get("previewUrl")
    return (u.strip(), "preview") if isinstance(u, str) and u.strip() else ("", "")

def _ExtFromCt(ct):
    ct = (ct or "").lower().split(";", 1)[0].strip()
    if ct in ("audio/mpeg", "audio/mp3"): return "mp3"
    if ct in ("audio/aac", "audio/x-aac"): return "aac"
    if ct in ("audio/mp4", "audio/m4a", "audio/x-m4a"): return "m4a"
    if ct in ("audio/ogg", "application/ogg"): return "ogg"
    if ct in ("audio/wav", "audio/x-wav"): return "wav"
    if ct in ("audio/flac", "audio/x-flac"): return "flac"
    return ""

def _ExtFromUrl(url):
    u = (url or "").split("?", 1)[0].split("#", 1)[0]
    m = re.search(r"\.([a-zA-Z0-9]{2,5})$", u)
    if not m:
        return ""
    e = m.group(1).lower()
    if e in ("mp3", "m4a", "aac", "ogg", "wav", "flac", "mp4"):
        return "m4a" if e == "mp4" else e
    return ""

def download(song, outDir=CacheDir):
    os.makedirs(outDir, exist_ok=True)

    url, q = _PickBestUrl(song)
    if not url:
        sid = (song or {}).get("id") or (song or {}).get("key") or ""
        if sid:
            try:
                song = resolve(sid)
                url, q = _PickBestUrl(song)
            except:
                pass
    if not url:
        return None

    sid = (song or {}).get("id") or (song or {}).get("key") or str(int(time.time() * 1000))
    title = _SafeName((song or {}).get("title") or (song or {}).get("name") or sid)
    artist = _SafeName((song or {}).get("artist") or (song or {}).get("artistName") or "")
    base = f"{title}-{artist}" if artist else title

    h = H()
    h["Accept"] = "*/*"
    r = requests.get(url, headers=h, timeout=TimeoutSec, stream=True, allow_redirects=True)
    if r.status_code != 200:
        return None

    ct = r.headers.get("Content-Type", "")
    ext = _ExtFromCt(ct) or _ExtFromUrl(url) or ("flac" if q == "lossless" else "mp3")
    tmp = os.path.join(outDir, f"tmp_{sid}_{int(time.time()*1000)}.{ext}")
    final = os.path.join(outDir, f"nct_{base}_{sid}.{ext}")

    total = 0
    try:
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=256 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                f.write(chunk)
        if total < 4096:
            try:
                os.remove(tmp)
            except:
                pass
            return None
        try:
            if os.path.exists(final):
                os.remove(final)
        except:
            pass
        os.replace(tmp, final)
        return final
    except:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except:
            pass
        return None