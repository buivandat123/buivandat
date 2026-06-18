from dto.index import *

CACHE_DIR = "assets/cache"
MAX_FILE_SIZE_MB = 9999
MAX_WORKERS = 5
CHUNK_SIZE = 16384
TIMEOUT = 60

DownloadPlatf = "download"

os.makedirs(CACHE_DIR, exist_ok=True)

def ffmpegPath():
    config = databaseReader()
    return (config.get("ffmpegPath") or "ffmpeg").strip().strip('"')

def FormatCount(count):
    try:
        count = int(count)
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        if count >= 1000:
            return f"{count/1000:.1f}K"
        return str(count)
    except:
        return "0"

def IsTiktokUrl(url):
    u = (url or "").lower()
    return "tiktok.com" in u or "vt.tiktok.com" in u

def IsSpotifyUrl(url):
    u = (url or "").lower()
    return "spotify.com" in u or "open.spotify.com" in u

def GetPlatformInfo(url):
    u = (url or "").lower()
    if "tiktok.com" in u or "vt.tiktok.com" in u:
        return "TikTok", "tiktok"
    if "facebook.com" in u or "fb.watch" in u or "fb.com" in u:
        return "Facebook", "facebook"
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube", "youtube"
    if "threads.net" in u or "threads.com" in u:
        return "Threads", "threads"
    if "instagram.com" in u:
        return "Instagram", "instagram"
    if "soundcloud.com" in u:
        return "SoundCloud", "soundcloud"
    if "spotify.com" in u or "open.spotify.com" in u:
        return "Spotify", "spotify"
    if "capcut.com" in u:
        return "CapCut", "capcut"
    return "Other", "video"

def EnsureMediaCache(this):
    if not hasattr(this, "MediaCache"):
        from functions.engine.data.mediaEngine import MediaCache
        this.MediaCache = MediaCache()

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

def IsAliveUrl(this, url):
    try:
        return bool(url) and this.MediaCache.isAlive(url)
    except:
        return False

def NormUrl(u):
    return str(u or "").strip()

def HashUrl(u):
    s = NormUrl(u)
    if not s:
        return ""
    try:
        return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()
    except:
        return "".join(c for c in s if c.isalnum())[:40]

def BuildDownloadSid(platformKey, url):
    hk = HashUrl(url)
    pk = "".join(c for c in str(platformKey or "other") if c.isalnum() or c in ("_", "-")).lower()[:24]
    return f"{pk}_{hk[:32] if hk else str(int(time.time()*1000))}"

def BuildCaption(platformName, title, uploader):
    t = (str(title or "Media"))[:100]
    up = (str(uploader or "Unknown"))[:60]
    return f"Source: {platformName}\nTitle: {t}\nBy: {up}"

def GetCachedDownload(this, sid):
    EnsureMediaCache(this)
    cache = this.MediaCache.get(DownloadPlatf, sid) or {}
    fileUrl = CacheGet(cache, "fileUrl")
    if fileUrl and not IsAliveUrl(this, fileUrl):
        fileUrl = None
    audioFileUrl = CacheGet(cache, "audioFileUrl")
    if audioFileUrl and not IsAliveUrl(this, audioFileUrl):
        audioFileUrl = None
    imageHdList = CacheGet(cache, "imageHdList") or []
    if isinstance(imageHdList, list) and imageHdList:
        imageHdList = [u for u in imageHdList if IsAliveUrl(this, u)]
    else:
        imageHdList = []
    meta = CacheGet(cache, "meta", {}) if isinstance(cache, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    return {"cache": cache, "fileUrl": fileUrl, "audioFileUrl": audioFileUrl, "imageHdList": imageHdList, "meta": meta}

def SetCachedDownload(this, sid, meta, fileUrl=None, audioFileUrl=None, imageHdList=None):
    EnsureMediaCache(this)
    pk = str((meta or {}).get("downloadPlatform") or "other").lower()
    shell = {"downloadPlatform": pk, "download": {pk: dict(meta or {})}}
    if audioFileUrl:
        shell["audioFileUrl"] = audioFileUrl
    if imageHdList is not None:
        shell["imageHdList"] = imageHdList if isinstance(imageHdList, list) else []
    this.MediaCache.set(DownloadPlatf, sid, shell, fileUrl)

def FetchTiktokInfo(tiktokUrl):
    maxRetries = 3
    for attempt in range(maxRetries):
        try:
            apiUrl = f"https://www.tikwm.com/api/?url={tiktokUrl}"
            r = requests.get(apiUrl, timeout=15)
            r.raise_for_status()
            data = r.json()
            if data.get("code") == 0 and data.get("data"):
                v = data["data"]
                m = v.get("music_info", {}) or {}
                images = v.get("images", []) or []
                return {
                    "video_url": v.get("play"),
                    "audio_url": m.get("play") or v.get("music"),
                    "duration": v.get("duration", 0),
                    "title": v.get("title", "TikTok"),
                    "author": (v.get("author", {}) or {}).get("nickname", "Unknown"),
                    "thumbnail": v.get("cover"),
                    "images": images,
                    "is_image": len(images) > 0
                }
        except Exception as e:
            if attempt == maxRetries - 1:
                try:
                    logger.errorMeta(f"[TikTok API] Error after {maxRetries} retries: {e}")
                except:
                    pass
            else:
                time.sleep(1)
    return None

def FetchSpotifyZeid(url):
    apiUrl = "https://api.zeidteam.xyz/media-downloader/atd2"
    r = requests.get(apiUrl, params={"url": url}, timeout=20)
    r.raise_for_status()
    j = r.json()
    if not j or not j.get("success") or not j.get("data"):
        raise Exception("Spotify API failed")
    d = j["data"] or {}
    musicUrl = d.get("music")
    if not musicUrl:
        att = d.get("attachment") or []
        if att and isinstance(att, list):
            musicUrl = (att[0] or {}).get("url")
    if not musicUrl:
        raise Exception("Spotify API missing music url")
    dur = d.get("duration", "0:0")
    try:
        parts = str(dur).strip().split(":")
        if len(parts) == 2:
            duration = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            duration = 0
    except:
        duration = 0
    return {"audio_url": musicUrl, "title": d.get("title") or "Spotify", "author": d.get("author") or d.get("artist") or "Unknown", "thumbnail": d.get("thumbnail"), "duration": duration}

def ParseDurationSec(x):
    s = str(x or "").strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except:
        pass
    parts = [p for p in s.split(":") if p.strip().isdigit()]
    if not parts:
        return 0
    nums = [int(p) for p in parts[-3:]]
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return nums[0] * 3600 + nums[1] * 60 + nums[2]

def NormalizeAioInfo(PlatformKey, AioInfo):
    j = AioInfo if isinstance(AioInfo, dict) else {}
    Meta = j.get("meta") if isinstance(j.get("meta"), dict) else {}
    Title = j.get("title") or Meta.get("title")
    Uploader = j.get("uploader") or j.get("author") or Meta.get("uploader") or Meta.get("author")
    Thumb = j.get("thumbnail") or j.get("thumb") or Meta.get("thumbnail") or Meta.get("thumb")
    Dur = j.get("duration") or Meta.get("duration") or 0
    Dur = ParseDurationSec(Dur)
    return {"downloadPlatform": PlatformKey, "title": Title or "Media", "uploader": Uploader or "Unknown", "thumbnail": Thumb, "duration": Dur, "width": 1080, "height": 1920}

def HasFfmpeg(FfmpegPath=None):
    p = (FfmpegPath or ffmpegPath() or "").strip().strip('"')
    try:
        if p and os.path.exists(p):
            return True
    except:
        pass
    try:
        if p and shutil.which(p):
            return True
    except:
        pass
    return bool(shutil.which("ffmpeg") or shutil.which("ffmpeg.exe"))

def GetFfprobePath(FfmpegPath=None):
    p = (FfmpegPath or ffmpegPath() or "").strip().strip('"')
    if not p:
        return shutil.which("ffprobe") or shutil.which("ffprobe.exe")

    base = os.path.basename(p).lower()
    if base in ("ffprobe", "ffprobe.exe") and os.path.exists(p):
        return p

    d = os.path.dirname(p) if os.path.dirname(p) else ""
    if d:
        cand = os.path.join(d, "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.exists(cand):
            return cand

    return shutil.which("ffprobe") or shutil.which("ffprobe.exe")

def GetVideoMetaByFfprobe(FilePath, FfmpegPath=None):
    Probe = GetFfprobePath(FfmpegPath)
    if not Probe or not FilePath or not os.path.exists(FilePath):
        return None
    Cmd = [Probe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", FilePath]
    try:
        Out = subprocess.check_output(Cmd, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore")
        j = json.loads(Out or "{}")
        Streams = j.get("streams") or []
        Fmt = j.get("format") or {}
        v = next((s for s in Streams if (s.get("codec_type") or "").lower() == "video"), None)
        if not v:
            return None
        w = int(v.get("width") or 0) or 0
        h = int(v.get("height") or 0) or 0
        Dur = v.get("duration") or Fmt.get("duration")
        try:
            Dur = float(Dur or 0)
        except:
            Dur = 0.0
        Rot = v.get("tags", {}).get("rotate")
        try:
            Rot = int(Rot) if Rot is not None else 0
        except:
            Rot = 0
        if Rot in (90, 270) and w and h:
            w, h = h, w
        return {"width": w, "height": h, "duration": Dur}
    except:
        return None

def DownloadFiles(Url, FileExtension="mp4"):
    if not Url:
        return None
    try:
        Headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*", "Connection": "keep-alive"}
        r = requests.get(Url, timeout=TIMEOUT, stream=True, headers=Headers, allow_redirects=True)
        r.raise_for_status()
        Name = f"{os.getpid()}_{int(time.time()*1000000)}.{FileExtension}"
        Path = os.path.join(CACHE_DIR, Name)
        with open(Path, "wb") as f:
            for Chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if Chunk:
                    f.write(Chunk)
        if not os.path.exists(Path) or os.path.getsize(Path) <= 0:
            try:
                os.remove(Path)
            except:
                pass
            return None
        return Path
    except Exception as e:
        try:
            logger.errorMeta(f"Download file error: {e}")
        except:
            pass
        return None

def DownloadMultipleImagesParallel(ImageUrls: List[str]) -> List[str]:
    Urls = [u for u in (ImageUrls or []) if u]
    if not Urls:
        return []
    Out = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as Ex:
        Fts = [Ex.submit(DownloadFiles, u, "jpg") for u in Urls]
        for Ft in as_completed(Fts):
            try:
                p = Ft.result()
                if p:
                    Out.append(p)
            except Exception as e:
                try:
                    logger.errorMeta(f"Image download error: {e}")
                except:
                    pass
    return Out

def ExtOfPath(Path):
    try:
        return os.path.splitext(str(Path))[1].lower().lstrip(".")
    except:
        return ""

def ClassifyPaths(Paths: List[str]):
    Img = {"jpg", "jpeg", "png", "webp", "bmp", "gif"}
    Vid = {"mp4", "mkv", "webm", "mov", "m4v", "avi", "flv"}
    Aud = {"mp3", "m4a", "aac", "opus", "ogg", "wav", "flac"}
    V, I, A, O = [], [], [], []
    for p in (Paths or []):
        try:
            if not p or not os.path.exists(p) or os.path.getsize(p) <= 0:
                continue
            Ext = ExtOfPath(p)
            (I if Ext in Img else V if Ext in Vid else A if Ext in Aud else O).append(p)
        except:
            pass

    def KeySort(x):
        try:
            b = os.path.basename(x)
            n = "".join(c for c in b if c.isdigit())
            return (int(n) if n else 10**18, b.lower())
        except:
            return (10**18, str(x))

    V.sort(key=KeySort); I.sort(key=KeySort); A.sort(key=KeySort); O.sort(key=KeySort)
    return {"videos": V, "images": I, "audios": A, "others": O}

def TryAioDown(Url, IsAudio=False, PrintLog=True):
    Cmd = ["aio-down", Url, "--paths", CACHE_DIR, "--timeout", str(TIMEOUT), "--retries", "2", "--all"]
    Paths, Info, Buf, InJson = [], None, [], False

    def AddPath(p):
        if not p:
            return
        p = str(p).strip().strip('"').strip()
        if p and os.path.exists(p) and os.path.getsize(p) > 0:
            Paths.append(p)

    try:
        Proc = subprocess.Popen(Cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for Line in iter(Proc.stdout.readline, ""):
                if not Line:
                    break
                if PrintLog:
                    try:
                        print(Line, end="")
                    except:
                        pass
                s = Line.rstrip("\r\n")

                if "SAVED ->" in s:
                    try:
                        Part = s.split("SAVED ->", 1)[1].strip()
                        AddPath(Part.split(" bytes=", 1)[0].strip())
                    except:
                        pass

                if s.lstrip().startswith("{"):
                    InJson, Buf = True, [s]
                    continue

                if InJson:
                    Buf.append(s)
                    if s.strip() == "}":
                        InJson = False
                        try:
                            j = json.loads("\n".join(Buf))
                            if isinstance(j, dict):
                                Info = j.get("json") if isinstance(j.get("json"), dict) else j
                                Pth = j.get("paths") if isinstance(j.get("paths"), list) else None
                                if Pth:
                                    for x in Pth:
                                        AddPath(x)
                        except:
                            pass
        finally:
            try:
                Proc.stdout.close()
            except:
                pass

        try:
            Proc.wait(timeout=TIMEOUT + 30)
        except:
            try:
                Proc.kill()
            except:
                pass

        if not Paths:
            return None

        Seen, Uniq = set(), []
        for p in Paths:
            if p not in Seen:
                Seen.add(p)
                Uniq.append(p)

        c = ClassifyPaths(Uniq)
        if IsAudio:
            if c["audios"]:
                Kind = "audio"
            elif c["videos"]:
                Kind = "video"
            elif c["images"]:
                Kind = "image"
            else:
                Kind = "other"
            return {"kind": Kind, "paths": Uniq, "classify": c, "info": Info}

        if c["videos"] and c["images"]:
            Kind = "mixed"
        elif c["videos"]:
            Kind = "video"
        elif c["images"]:
            Kind = "image"
        elif c["audios"]:
            Kind = "audio"
        else:
            Kind = "other"
        return {"kind": Kind, "paths": Uniq, "classify": c, "info": Info}
    except Exception as e:
        try:
            logger.errorMeta(f"AioDown error: {e}")
        except:
            pass
        return None

def DownloadYtdlp(Url, IsAudio=False):
    InfoOpts = {"quiet": True, "no_warnings": True, "extract_flat": False, "skip_download": True}
    with yt_dlp.YoutubeDL(InfoOpts) as Ydl:
        Info = Ydl.extract_info(Url, download=False)
        Size = Info.get("filesize_approx") or Info.get("filesize")
        if Size and Size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise Exception(f"File size exceeds {MAX_FILE_SIZE_MB}MB.")

    InfoId = Info.get("id", "media")
    SafeId = "".join(filter(str.isalnum, str(InfoId)))[:30]
    OutTmpl = os.path.join(CACHE_DIR, f"dl_{SafeId}.%(ext)s")
    FFMPEG_PATH = ffmpegPath()
    HasFf = HasFfmpeg(FFMPEG_PATH)

    def PickOk(p):
        return p if p and os.path.exists(p) and os.path.getsize(p) > 0 else None

    def Cleanup(prepared):
        if not prepared:
            return
        Base = os.path.splitext(prepared)[0]
        for Ext in [".mp4", ".mkv", ".webm", ".m4a", ".opus", ".aac", ".mp3", ".part", ".ytdl"]:
            p = Base + Ext
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

    def Run(fmt, post, mergeFmt):
        Opts = {
            "format": fmt,
            "outtmpl": OutTmpl,
            "quiet": True,
            "no_warnings": True,
            "retries": 8,
            "fragment_retries": 8,
            "concurrent_fragment_downloads": 5,
            "http_chunk_size": 10485760,
            "socket_timeout": 20,
            "geo_bypass": True,
            "forceipv4": True,
            "noplaylist": True,
            "overwrites": True,
            "continuedl": True,
            "merge_output_format": mergeFmt,
            "postprocessors": post,
            "ffmpeg_location": FFMPEG_PATH if FFMPEG_PATH else None,
            "http_headers": {"User-Agent": "Mozilla/5.0", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9,vi;q=0.8", "Connection": "keep-alive"},
        }
        with yt_dlp.YoutubeDL(Opts) as Ydl:
            Inf = Ydl.extract_info(Url, download=True)
            Fn = Ydl.prepare_filename(Inf)
            return Fn, Inf

    if IsAudio:
        Tries = [("bestaudio/best", [{"key": "FFmpegExtractAudio", "preferredcodec": "aac"}], None),
                 ("bestaudio[ext=m4a]/bestaudio/best", [{"key": "FFmpegExtractAudio", "preferredcodec": "aac"}], None)] if HasFf else \
                [("bestaudio[ext=m4a]/bestaudio/best", [], None),
                 ("bestaudio/best", [], None)]
    else:
        Tries = [("bestvideo[filesize<70M][vcodec^=avc1]+bestaudio/best", [], "mp4"),
                 ("bestvideo[filesize<70M]+bestaudio/best", [], "mp4"),
                 ("best[ext=mp4][vcodec!=none][acodec!=none][filesize<70M]/best", [], "mp4")] if HasFf else \
                [("best[ext=mp4][vcodec!=none][acodec!=none][filesize<70M]/best[ext=mp4][vcodec!=none][acodec!=none]/best", [], None),
                 ("best[ext=mp4][vcodec!=none][acodec!=none]/best", [], None)]

    LastErr = None
    for Fmt, Post, MergeFmt in Tries:
        Prepared = None
        try:
            Prepared, Inf = Run(Fmt, Post, MergeFmt)
            Base = os.path.splitext(Prepared)[0]
            if IsAudio:
                exts = [".aac", ".m4a", ".mp3", ".opus"] if HasFf else [".m4a", ".webm", ".opus", ".aac", ".mp3"]
                for Ext in exts:
                    p = PickOk(Base + Ext)
                    if p:
                        return p, Inf
            Ok = PickOk(Prepared)
            if Ok:
                return Ok, Inf
            Cleanup(Prepared)
            LastErr = Exception("The downloaded file is empty")
        except Exception as e:
            LastErr = e
            Cleanup(Prepared)

    raise LastErr if LastErr else Exception("Download failed.")

def UploadPathToFileUrl(This, Path, ThreadId, Type):
    Up = This.uploadAttachment(Path, ThreadId, Type)
    return (Up.get("fileUrl") if Up else None)

def UploadImagesToHdUrls(This, ImagePaths, ThreadId, Type):
    if not ImagePaths:
        return []
    Hd = []
    for p in ImagePaths:
        try:
            Up = This.uploadImage(p, ThreadId, Type)
            u = Up.get("hdUrl") if Up else None
            if u:
                Hd.append(u)
        except:
            pass
    return Hd

def SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, FilePath, ImagePaths, AudioPath, IsAudio, ThreadId, Type, UserId):
    Title = (Info.get("title") if isinstance(Info, dict) else None) or "Media"
    Uploader = (Info.get("uploader") if isinstance(Info, dict) else None) or (Info.get("author") if isinstance(Info, dict) else None) or "Unknown"
    Caption = BuildCaption(PlatformName, Title, Uploader)

    BaseMeta = {
        "downloadPlatform": PlatformKey,
        "title": Title,
        "uploader": Uploader,
        "thumbnail": (Info.get("thumbnail") if isinstance(Info, dict) else None),
        "width": int((Info.get("width") if isinstance(Info, dict) else 1080) or 1080),
        "height": int((Info.get("height") if isinstance(Info, dict) else 1920) or 1920),
    }

    if IsAudio:
        Path = AudioPath or FilePath
        if not Path or not os.path.exists(Path):
            raise Exception("Audio download failed.")
        FileUrl = (This.uploadAttachment(Path, ThreadId, Type) or {}).get("fileUrl")
        try:
            os.remove(Path)
        except:
            pass
        if not FileUrl:
            raise Exception("Upload voice failed.")
        Meta = dict(BaseMeta)
        Meta["kind"] = "audio"
        try:
            Meta["duration"] = int((Info.get("duration") if isinstance(Info, dict) else 0) or 0)
        except:
            Meta["duration"] = 0
        SetCachedDownload(This, Sid, Meta, fileUrl=FileUrl)
        This.sendVoice(FileUrl, ThreadId, Type)
        return

    VideoFileUrl, ImageHdList = None, []

    if FilePath and os.path.exists(FilePath):
        Dur = Info.get("duration", 0) if isinstance(Info, dict) else 0
        try:
            Dur = float(Dur or 0)
        except:
            Dur = 0.0

        w, h = BaseMeta["width"], BaseMeta["height"]
        Probe = GetVideoMetaByFfprobe(FilePath, ffmpegPath())
        if Probe:
            if Probe.get("width"):
                w = int(Probe["width"])
            if Probe.get("height"):
                h = int(Probe["height"])
            if Probe.get("duration"):
                Dur = float(Probe["duration"])

        VideoFileUrl = UploadPathToFileUrl(This, FilePath, ThreadId, Type)
        try:
            os.remove(FilePath)
        except:
            pass
        if not VideoFileUrl:
            raise Exception("Upload video failed.")

        DurMs = int(float(Dur or 0) * 1000)
        MetaVid = dict(BaseMeta)
        MetaVid["kind"] = "video"
        MetaVid["durationMs"] = int(DurMs or 0)
        MetaVid["width"] = int(w or 1080)
        MetaVid["height"] = int(h or 1920)

        This.sendVideo(VideoFileUrl, thumbnailUrl=MetaVid.get("thumbnail"), duration=int(DurMs or 0),
                       message=Message(text=Caption), threadId=ThreadId, type=Type, width=int(w or 1080), height=int(h or 1920))
        BaseMeta = MetaVid

    if ImagePaths:
        try:
            ImageHdList = UploadImagesToHdUrls(This, ImagePaths, ThreadId, Type)
            if ImageHdList:
                if len(ImageHdList) == 1:
                    This.sendImage(imageUrl=ImageHdList[0], message=Message(text=Caption), threadId=ThreadId, type=Type, width=1080, height=1080)
                else:
                    This.sendMention(Caption, UserId, ThreadId, Type)
                    This.sendMultiImage(imageUrlList=ImageHdList, message=Message(text=None), threadId=ThreadId, type=Type)
        finally:
            for p in ImagePaths:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except:
                        pass

    if VideoFileUrl or ImageHdList:
        MetaFinal = dict(BaseMeta)
        MetaFinal["kind"] = "mixed" if (VideoFileUrl and ImageHdList) else ("video" if VideoFileUrl else "image")
        SetCachedDownload(This, Sid, MetaFinal, fileUrl=VideoFileUrl, imageHdList=ImageHdList)
        return

    raise Exception("Download failed.")

def ProcessSingleLink(i, Url, IsAudio, ThreadId, Type, This, Data, UserId):
    try:
        EnsureMediaCache(This)
        PlatformName, PlatformKey = GetPlatformInfo(Url)
        Sid = BuildDownloadSid(PlatformKey, Url)
        Cached = GetCachedDownload(This, Sid) or {}

        Meta0 = (Cached.get("meta") or {}) if isinstance(Cached.get("meta"), dict) else {}
        Cache0 = Cached.get("cache") or {}
        if isinstance(Cache0, dict) and isinstance(Cache0.get("download"), dict):
            Sub = Cache0["download"].get(PlatformKey)
            if isinstance(Sub, dict):
                Meta0 = dict(Sub)

        Title0 = Meta0.get("title") or "Media"
        Uploader0 = Meta0.get("uploader") or "Unknown"
        Caption0 = BuildCaption(PlatformName, Title0, Uploader0)
        Kind0 = (Meta0.get("kind") or "").lower()

        if IsAudio and Cached.get("fileUrl") and Kind0 == "audio":
            This.sendVoice(Cached["fileUrl"], ThreadId, Type)
            return

        if (not IsAudio) and Cached.get("fileUrl") and Kind0 in ("video", "mixed"):
            Dur = int(Meta0.get("durationMs") or 0)
            w = int(Meta0.get("width") or 1080)
            h = int(Meta0.get("height") or 1920)
            This.sendVideo(Cached["fileUrl"], thumbnailUrl=Meta0.get("thumbnail"), duration=Dur,
                           message=Message(text=Caption0), threadId=ThreadId, type=Type, width=w, height=h)
            HdList = Cached.get("imageHdList") or []
            if HdList:
                if len(HdList) == 1:
                    This.sendImage(imageUrl=HdList[0], message=Message(text=Caption0), threadId=ThreadId, type=Type, width=1080, height=1080)
                else:
                    This.sendMultiImage(imageUrlList=HdList, message=Message(text=Caption0), threadId=ThreadId, type=Type)
            return

        if (not IsAudio) and Kind0 == "image":
            HdList = Cached.get("imageHdList") or []
            if HdList:
                if len(HdList) == 1:
                    This.sendImage(imageUrl=HdList[0], message=Message(text=Caption0), threadId=ThreadId, type=Type, width=1080, height=1080)
                else:
                    This.sendMention(Caption0, UserId, ThreadId, Type)
                    This.sendMultiImage(imageUrlList=HdList, message=None, threadId=ThreadId, type=Type)
                if Cached.get("audioFileUrl"):
                    This.sendVoice(Cached["audioFileUrl"], ThreadId, Type)
                return

        FilePath, Info = None, {}
        ImagePaths, AudioPath = [], None

        if IsTiktokUrl(Url):
            Tk = FetchTiktokInfo(Url)
            if not Tk:
                This.sendMFailed("Failed to fetch TikTok info.", UserId, ThreadId, Type)
                return

            Info = {"title": Tk.get("title") or "TikTok", "author": Tk.get("author") or "Unknown", "uploader": Tk.get("author") or "Unknown",
                    "duration": Tk.get("duration") or 0, "thumbnail": Tk.get("thumbnail"), "width": 1080, "height": 1920}

            if (IsAudio or Tk.get("is_image")) and Tk.get("audio_url"):
                AudioPath = DownloadFiles(Tk["audio_url"], "aac")

            if IsAudio:
                SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, None, [], AudioPath, True, ThreadId, Type, UserId)
                return

            if Tk.get("is_image") and Tk.get("images"):
                ImagePaths = DownloadMultipleImagesParallel(Tk["images"])
                SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, None, ImagePaths, AudioPath, False, ThreadId, Type, UserId)
                return

            if Tk.get("video_url"):
                FilePath = DownloadFiles(Tk["video_url"], "mp4")
                SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, FilePath, [], AudioPath, False, ThreadId, Type, UserId)
                return

            raise Exception("TikTok download failed.")

        Aio = TryAioDown(Url, IsAudio=IsAudio, PrintLog=True)
        if Aio and isinstance(Aio.get("classify"), dict):
            c = Aio["classify"]
            Info = NormalizeAioInfo(PlatformKey, Aio.get("info") or {})
            V = c.get("videos") or []
            I = c.get("images") or []
            A = c.get("audios") or []

            if IsAudio:
                if A:
                    SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, None, [], A[0], True, ThreadId, Type, UserId)
                    return
                if V:
                    SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, V[0], [], None, False, ThreadId, Type, UserId)
                    return
                if I:
                    SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, None, I, None, False, ThreadId, Type, UserId)
                    return
                raise Exception("AioDown audio mode no media.")

            if V:
                FilePath = V[0]
            if I:
                ImagePaths = I
            if (not FilePath) and (not ImagePaths) and A:
                SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, None, [], A[0], True, ThreadId, Type, UserId)
                return
            if not FilePath and not ImagePaths:
                raise Exception("AioDown no media.")
            SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, FilePath, ImagePaths, None, False, ThreadId, Type, UserId)
            return

        FilePath, InfoY = DownloadYtdlp(Url, IsAudio)
        Info = InfoY if isinstance(InfoY, dict) else {}
        Info = {"title": Info.get("title") or "Media", "uploader": Info.get("uploader") or Info.get("author") or "Unknown",
                "author": Info.get("uploader") or Info.get("author") or "Unknown", "duration": Info.get("duration") or 0,
                "thumbnail": Info.get("thumbnail"), "width": 1080, "height": 1920}
        SendDownloaded(This, PlatformName, PlatformKey, Sid, Info, FilePath, [], None, IsAudio, ThreadId, Type, UserId)

    except Exception as e:
        try:
            logger.errorMeta(f"Download error for {Url}: {e}")
        except:
            pass