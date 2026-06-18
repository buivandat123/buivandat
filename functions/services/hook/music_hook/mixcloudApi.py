from dto.index import *
from functions.engine.data.data import databaseReader
import shutil

MixcloudApiBase = "https://api.mixcloud.com"
CacheDir = "./assets/cache"
os.makedirs(CacheDir, exist_ok=True)

TimeoutSec = 15
UserAgent = "Mozilla/5.0"
_cfg_ff = (databaseReader().get("ffmpegPath") or "").strip().strip('"')
FfmpegExe = _cfg_ff if _cfg_ff else (shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg")

def Norm(s):
    return (s or "").strip()

def NowMs():
    return int(time.time() * 1000)

def H():
    return {"User-Agent": UserAgent, "Accept": "application/json,*/*"}

def Get(pathOrUrl, params=None):
    u = Norm(pathOrUrl)
    if not u:
        raise RuntimeError("MixcloudInvalidPathOrUrl")
    if u.startswith("http://") or u.startswith("https://"):
        url = u
    else:
        p = u if u.startswith("/") else "/" + u
        url = f"{MixcloudApiBase}{p}"
    r = requests.get(url, params=params or {}, headers=H(), timeout=TimeoutSec, allow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError(f"MixcloudApiError status={r.status_code} body={r.text}")
    return r.json()

def NormalizeKeyOrUrl(v):
    s = Norm(v)
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        u = urlparse(s)
        if u.netloc.endswith("mixcloud.com"):
            return MixcloudApiBase.rstrip("/") + (u.path or "/")
        return s
    if not s.startswith("/"):
        s = "/" + s
    return MixcloudApiBase.rstrip("/") + s

def CloudcastKeyFromLinkOrKey(linkOrKey):
    s = Norm(linkOrKey)
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        u = urlparse(s)
        if u.netloc.endswith("mixcloud.com"):
            p = u.path or ""
            if not p.startswith("/"):
                p = "/" + p
            return p
        return None
    if s.startswith("/"):
        return s
    if "/" in s:
        return "/" + s
    return None

def SafeInt(v):
    try:
        return int(v)
    except:
        return 0

def PickCover(pictures):
    pics = pictures or {}
    return Norm(pics.get("extra_large")) or Norm(pics.get("large")) or Norm(pics.get("medium")) or Norm(pics.get("small")) or None

def CloudcastToSong(x):
    user = (x or {}).get("user") or {}
    pics = (x or {}).get("pictures") or {}
    key = (x or {}).get("key") or (x or {}).get("path") or ""
    webUrl = Norm((x or {}).get("url"))
    apiUrl = NormalizeKeyOrUrl(key or webUrl) or None
    title = Norm((x or {}).get("name") or (x or {}).get("title"))
    username = Norm(user.get("username"))
    artist = Norm(user.get("name")) or username or None
    createdTime = Norm((x or {}).get("created_time"))
    duration = SafeInt((x or {}).get("audio_length") or (x or {}).get("duration") or 0)
    like = SafeInt((x or {}).get("favorite_count") or (x or {}).get("favorites_count") or 0)
    listen = SafeInt((x or {}).get("play_count") or 0)
    comment = SafeInt((x or {}).get("comment_count") or 0)
    cover = PickCover(pics)
    return {
        "id": key or apiUrl or webUrl or None,
        "title": title or None,
        "link": webUrl or None,
        "artist": artist,
        "cover": cover,
        "duration": duration,
        "like": like,
        "listen": listen,
        "comment": comment,
        "explicit": None,
        "previewUrl": None,
        "uri": key or None,
        "isPlayable": None,
        "key": key or None,
        "apiUrl": apiUrl,
        "username": username or None,
        "createdTime": createdTime or None,
    }

def Resolve(linkOrKey):
    key = CloudcastKeyFromLinkOrKey(linkOrKey)
    if not key:
        raise RuntimeError("InvalidMixcloudCloudcastLinkOrKey")
    j = Get(key, params={"_ts": NowMs()})
    return CloudcastToSong(j)

def SearchSong(q, limit=10, offset=0):
    qq = Norm(q)
    if not qq:
        return []
    params = {"q": qq, "type": "cloudcast", "limit": int(limit), "offset": int(offset), "_ts": NowMs()}
    j = Get("/search/", params=params)
    items = (j or {}).get("data") or []
    return [CloudcastToSong(x) for x in items]

def SafeName(s, maxLen=120):
    s = Norm(s)
    if not s:
        s = str(NowMs())
    s = re.sub(r"[^\w\-. ]+", "_", s, flags=re.UNICODE).strip(" ._-")
    if not s:
        s = str(NowMs())
    return s[:maxLen]

def LatestFile(dirPath, afterTs=None):
    try:
        best = None
        bestM = -1
        for name in os.listdir(dirPath):
            p = os.path.join(dirPath, name)
            if not os.path.isfile(p):
                continue
            m = os.path.getmtime(p)
            if afterTs is not None and m < afterTs:
                continue
            if m > bestM:
                bestM = m
                best = p
        return best
    except:
        return None

def Download(song, timeoutSec=0, audioFormat="mp3"):
    link = Norm((song or {}).get("link"))
    if not link:
        return {"ok": False, "error": "no_link"}

    title = SafeName((song or {}).get("title") or (song or {}).get("id") or "mixcloud")
    outTpl = os.path.join(CacheDir, f"{title}.%(ext)s")
    before = time.time()

    cmd = ["yt-dlp", "-N", "8", "--no-playlist", "--no-warnings", "--ffmpeg-location", FfmpegExe, "-o", outTpl]

    af = Norm(audioFormat).lower()
    if af and af != "source":
        cmd += ["--extract-audio", "--audio-format", af, "--audio-quality", "0"]

    cmd.append(link)

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=int(timeoutSec) if timeoutSec and timeoutSec > 0 else None,
            check=False,
        )
        if p.returncode != 0:
            return {
                "ok": False,
                "cmd": cmd,
                "returncode": p.returncode,
                "stdout": Norm(p.stdout),
                "stderr": Norm(p.stderr),
            }
        path = LatestFile(CacheDir, afterTs=before)
        return {
            "ok": True,
            "cmd": cmd,
            "returncode": p.returncode,
            "path": path,
            "stdout": Norm(p.stdout),
            "stderr": Norm(p.stderr),
        }
    except subprocess.TimeoutExpired as ex:
        return {"ok": False, "error": "timeout", "cmd": ex.cmd}
    except Exception as ex:
        return {"ok": False, "error": "exception", "message": str(ex)}