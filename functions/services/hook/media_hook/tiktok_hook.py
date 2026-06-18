from dto.index import *
from functions.engine.data.data import ReadServices, WriteService
from functions.services.artistcore.searchSongs import DrawSongsListCard, W, H
from functions.services.artistcore.songsCard import draw_song_card
from functions.engine.data.mediaEngine import MediaCache

Platf = "tiktok"
Timeout = 120
TikwmBase = "https://tikwm.com"

def ClientTikwm(proxy=None, timeout=25):
    return httpx.Client(
        timeout=timeout,
        proxy=proxy,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": TikwmBase + "/",
            "Origin": TikwmBase,
        },
        follow_redirects=True,
    )

def Pick(d, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def Short(s, n=60):
    s = (s or "").strip().replace("\n", " ")
    return (s[: n - 3] + "...") if len(s) > n else s

def FmtNum(n):
    try:
        n = int(n)
    except:
        return "0"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B".rstrip("0").rstrip(".")
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n/1_000:.1f}K".rstrip("0").rstrip(".")
    return str(n)

def NormalizeSearchItem(x):
    return {
        "id": str(x.get("video_id") or x.get("id") or ""),
        "desc": x.get("title") or x.get("desc") or "",
        "createTime": int(x.get("create_time") or x.get("createTime") or 0),
        "stat": {
            "playCount": int(x.get("play_count") or x.get("playCount") or 0),
            "diggCount": int(x.get("digg_count") or x.get("diggCount") or 0),
            "commentCount": int(x.get("comment_count") or x.get("commentCount") or 0),
            "shareCount": int(x.get("share_count") or x.get("shareCount") or 0),
            "downloadCount": int(x.get("download_count") or x.get("downloadCount") or 0),
        },
        "video": {
            "url": x.get("play") or x.get("video_url") or x.get("wmplay") or "",
            "cover": x.get("cover") or x.get("origin_cover") or "",
            "duration": int((x.get("duration") or 0) * 1000) or 1000,
            "type": "mp4",
            "quality": x.get("quality") or "auto",
        },
        "author": x.get("author") or {},
        "music": {
            "title": Pick(x, "music_info", "title", default="") or x.get("music_title") or "",
            "url": Pick(x, "music_info", "play", default="") or x.get("music") or "",
            "cover": Pick(x, "music_info", "cover", default="") or "",
            "author": Pick(x, "music_info", "author", default="") or "",
            "quality": "audio",
            "type": "mp3",
        },
    }

def SearchTikwm(keywords, limit=20, proxy=None):
    url = f"{TikwmBase}/api/feed/search"
    payload = {"keywords": keywords, "count": int(limit)}
    with ClientTikwm(proxy=proxy) as c:
        r = c.post(url, data=payload)
        if r.status_code != 200:
            return []
        j = r.json()
    items = Pick(j, "data", "videos", default=None) or Pick(j, "data", default=[]) or []
    out = []
    for it in items:
        v = NormalizeSearchItem(it)
        if v["id"]:
            out.append(v)
        if len(out) >= limit:
            break
    return out

def MakeTikTokUrlFromId(videoId):
    videoId = str(videoId or "").strip()
    if not videoId:
        return None
    if videoId.startswith("http://") or videoId.startswith("https://"):
        return videoId
    return f"https://www.tiktok.com/@tiktok/video/{videoId}"

def GetVideoInfoTikwm(tiktokUrl, proxy=None):
    url = f"{TikwmBase}/api/"
    payload = {"url": tiktokUrl}
    with ClientTikwm(proxy=proxy) as c:
        r = c.post(url, data=payload)
        if r.status_code != 200:
            return None
        j = r.json()
    data = j.get("data") or {}
    if not data:
        return None
    images = data.get("images") if isinstance(data.get("images"), list) else None
    isPhoto = bool(images)
    return {
        "id": str(data.get("id") or data.get("aweme_id") or ""),
        "desc": data.get("title") or data.get("desc") or "",
        "author": {
            "uniqueId": Pick(data, "author", "unique_id", default="") or Pick(data, "author", "uniqueId", default=""),
            "nickname": Pick(data, "author", "nickname", default="") or "",
        },
        "music": {
            "title": Pick(data, "music_info", "title", default="") or "",
            "url": Pick(data, "music_info", "play", default="") or data.get("music") or "",
            "cover": Pick(data, "music_info", "cover", default="") or "",
            "author": Pick(data, "music_info", "author", default="") or "",
            "quality": "audio",
            "type": "mp3",
        },
        "stat": {
            "playCount": int(data.get("play_count") or 0),
            "diggCount": int(data.get("digg_count") or 0),
            "commentCount": int(data.get("comment_count") or 0),
            "shareCount": int(data.get("share_count") or 0),
            "downloadCount": int(data.get("download_count") or 0),
            "collectCount": int(data.get("collect_count") or 0),
        },
        "type": "photo" if isPhoto else "video",
        "images": images or [],
        "video": None
        if isPhoto
        else {
            "url": data.get("play") or "",
            "wmUrl": data.get("wmplay") or "",
            "noWatermarkUrl": data.get("hdplay") or data.get("play") or "",
            "cover": data.get("cover") or "",
            "duration": int((data.get("duration") or 0) * 1000) or 1000,
            "type": "mp4",
            "quality": data.get("quality") or "auto",
        },
    }

def DownloadTikwmNoWatermark(tiktokUrl, proxy=None):
    info = GetVideoInfoTikwm(tiktokUrl, proxy=proxy)
    if not info:
        return None
    if info["type"] == "photo":
        return info
    v = info.get("video") or {}
    if not v.get("noWatermarkUrl") and v.get("url"):
        v["noWatermarkUrl"] = v["url"]
    info["video"] = v
    return info

def DownloadFile(url, outPath, proxy=None, timeout=120):
    os.makedirs(os.path.dirname(outPath) or ".", exist_ok=True)
    with httpx.Client(timeout=timeout, proxy=proxy, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as c:
        with c.stream("GET", url) as r:
            r.raise_for_status()
            with open(outPath, "wb") as f:
                for chunk in r.iter_bytes():
                    if chunk:
                        f.write(chunk)
    return outPath

def EnsureMediaCache(this):
    if hasattr(this, "MediaCache") and getattr(this, "MediaCache", None):
        return
    try:
        this.MediaCache = MediaCache(owner=this)
        return
    except:
        try:
            this.MediaCache = MediaCache()
        except:
            this.MediaCache = None

def CacheGet(cache, k, d=None):
    if not isinstance(cache, dict):
        return d
    v = cache.get(k)
    if v is not None:
        return v
    meta = cache.get("meta")
    if isinstance(meta, dict):
        v2 = meta.get(k)
        if v2 is not None:
            return v2
    return d

def IsAlive(this, url):
    try:
        return bool(url) and this.MediaCache and this.MediaCache.isAlive(url)
    except:
        return False

def GetFfmpegPath(this):
    try:
        r = databaseReader()
        p = r.get("ffmpegPath")
        if p:
            return str(p)
    except:
        pass
    return "/usr/bin/ffmpeg"

def GetVideoMeta(ffmpegPath, filePath):
    try:
        p = subprocess.run([ffmpegPath, "-hide_banner", "-i", filePath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        s = (p.stderr or "") + "\n" + (p.stdout or "")
    except:
        return {"duration": 0, "width": 1080, "height": 1920}

    durMs = 0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)(?:\.(\d+))?", s)
    if m:
        h = int(m.group(1) or 0)
        mi = int(m.group(2) or 0)
        se = int(m.group(3) or 0)
        frac = m.group(4) or "0"
        ms = int(frac[:3].ljust(3, "0")) if frac else 0
        durMs = ((h * 3600 + mi * 60 + se) * 1000) + ms

    w = 1080
    h2 = 1920
    for line in s.splitlines():
        if " Video:" in line or (line.strip().startswith("Stream #") and " Video:" in line):
            m2 = re.search(r"(\d{2,5})x(\d{2,5})", line)
            if m2:
                w = int(m2.group(1))
                h2 = int(m2.group(2))
                break

    return {"duration": int(durMs or 0), "width": int(w or 1080), "height": int(h2 or 1920)}

def DrawTikTokListCard(items, outPath, title="Kết quả TikTok", subtitle="Reply số hoặc: 1 audio"):
    def FmtMs(ms):
        ms = int(ms or 0)
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    rows = []
    for it in items:
        rows.append(
            {
                "title": Short(it.get("desc", "") or "TikTok", 42),
                "artist": (Pick(it, "author", "unique_id", default="") or Pick(it, "author", "uniqueId", default="") or Pick(it, "author", "nickname", default="") or "TikTok"),
                "duration": FmtMs(Pick(it, "video", "duration", default=0) or 0),
                "cover": Pick(it, "video", "cover", default="") or "",
            }
        )

    return DrawSongsListCard(
        [{"title": r["title"], "artist": r["artist"], "duration": r["duration"], "cover": r["cover"]} for r in rows],
        outPath,
        Title=title,
        SubTitle=subtitle,
        Source="TikTok",
    )