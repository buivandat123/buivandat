from dto.index import *
from functions.engine.data.mediaEngine import MediaCache
from functions.engine.data.data import databaseReader

MaxStickerSize = 700
WebpQuality = 95
Platf = "sticker"

def Clamp(v, a, b):
    return a if v < a else b if v > b else v

def ClampScale(scaleFactor):
    return Clamp(float(scaleFactor or 1.0), 0.1, 1.0)

def SquareCanvas(img, canvasSize, scaleFactor):
    canvasSize = int(canvasSize)
    sf = ClampScale(scaleFactor)
    inner = max(1, int(canvasSize * sf))

    w, h = img.size
    m = max(w, h)
    if m > inner:
        s = inner / m
        img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)

    out = Image.new("RGBA", (canvasSize, canvasSize), (0, 0, 0, 0))
    x = (canvasSize - img.size[0]) // 2
    y = (canvasSize - img.size[1]) // 2
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    out.paste(img, (x, y), img)
    return out

def RunCmd(cmd):
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def WriteTmp(data, suffix):
    p = tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name
    with open(p, "wb") as f:
        f.write(data)
    return p

def GuessSuffix(kind):
    if not kind:
        return ".bin"
    if kind.extension == "gif":
        return ".gif"
    if kind.extension == "webp":
        return ".webp"
    if kind.extension in ("jpg", "jpeg"):
        return ".jpg"
    if kind.extension == "png":
        return ".png"
    if kind.extension == "jxl":
        return ".jxl"
    if kind.mime and kind.mime.startswith("video"):
        return ".mp4"
    return "." + kind.extension

def ResizeKeepRatio(img, maxSize):
    w, h = img.size
    m = max(w, h)
    if m <= maxSize:
        return img
    s = maxSize / m
    return img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)

def CropSquare(img):
    w, h = img.size
    s = min(w, h)
    x0 = (w - s) // 2
    y0 = (h - s) // 2
    return img.crop((x0, y0, x0 + s, y0 + s))

def ApplyRoundCorner(img, percent):
    if percent <= 0:
        return img
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    w, h = img.size
    r = int(min(w, h) * percent / 200)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=r, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out

def ProcessImage(img, maxSize=MaxStickerSize, radiusPercent=0, sqr=False, scaleFactor=1.0):
    img = ResizeKeepRatio(img, maxSize)
    if sqr:
        img = CropSquare(img)
        img = SquareCanvas(img, maxSize, scaleFactor)
    else:
        if radiusPercent == 100:
            img = CropSquare(img)
    if radiusPercent > 0:
        img = ApplyRoundCorner(img, radiusPercent)
    return img

def BytesCreate(imageBytes, outputPath, xp=False, maxSize=MaxStickerSize, radiusPercent=0, isAnimation=False, sqr=False, scaleFactor=1.0):
    if xp:
        imageBytes = remove(imageBytes)
    img = Image.open(BytesIO(imageBytes))
    os.makedirs(os.path.dirname(outputPath), exist_ok=True)

    if getattr(img, "is_animated", False) or isAnimation:
        frames = []
        duration = max(10, int(getattr(img, "info", {}).get("duration", 66)))
        for frame in ImageSequence.Iterator(img):
            f = frame.convert("RGBA")
            f = ProcessImage(f, maxSize, radiusPercent, sqr=sqr, scaleFactor=scaleFactor)
            frames.append(f)
        frames[0].save(
            outputPath,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            quality=WebpQuality,
            method=6
        )
        return

    im = img.convert("RGBA")
    im = ProcessImage(im, maxSize, radiusPercent, sqr=sqr, scaleFactor=scaleFactor)
    im.save(outputPath, "WEBP", quality=WebpQuality, method=6)

def ffmpegPath():
    config = databaseReader()
    return config.get("ffmpegPath") or "ffmpeg"

def ConvertJxlToPngBytes(jxlBytes):
    tmpIn = WriteTmp(jxlBytes, ".jxl")
    tmpOut = tmpIn[:-4] + ".png"
    try:
        RunCmd([ffmpegPath(), "-y", "-i", tmpIn, tmpOut])
        with open(tmpOut, "rb") as f:
            return f.read()
    finally:
        for p in (tmpIn, tmpOut):
            try:
                os.remove(p)
            except:
                pass

def FfmpegToWebpAnim(inputPath, outputPath, fps=30, scale=480, seconds=30, q=95, sqr=False, scaleFactor=1.0):
    fps = int(fps)
    scale = int(scale)
    seconds = int(seconds)
    q = int(q)

    if sqr:
        sf = ClampScale(scaleFactor)
        inner = max(1, int(scale * sf))
        vf = (
            f"fps={fps},"
            f"crop='min(iw,ih)':'min(iw,ih)',"
            f"scale={inner}:{inner}:flags=lanczos,"
            f"pad={scale}:{scale}:(ow-iw)/2:(oh-ih)/2:color=0x00000000"
        )
    else:
        vf = f"fps={fps},scale={scale}:-1:flags=lanczos"

    cmd = [
        ffmpegPath(), "-y", "-i", inputPath,
        "-t", str(seconds),
        "-vf", vf,
        "-q:v", str(q),
        "-loop", "0",
        "-threads", "0",
        "-an",
        outputPath
    ]
    RunCmd(cmd)

def RoundWebpFrames(inputPath, outputPath, radiusPercent):
    with Image.open(inputPath) as im:
        isAnim = getattr(im, "is_animated", False)
        duration = max(10, int(getattr(im, "info", {}).get("duration", 66)))
        if isAnim:
            frames = []
            for frame in ImageSequence.Iterator(im):
                f = frame.convert("RGBA")
                f = ApplyRoundCorner(f, radiusPercent)
                frames.append(f)
            frames[0].save(
                outputPath,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0,
                quality=WebpQuality,
                method=6
            )
            return
        f = im.convert("RGBA")
        f = ApplyRoundCorner(f, radiusPercent)
        f.save(outputPath, "WEBP", quality=WebpQuality, method=6)

def SpinWebp(inputPath, outputPath, fps=60, seconds=6, q=90):
    denom = max(1, int(fps) * int(seconds))
    cmd = [
        ffmpegPath(), "-y",
        "-loop", "1",
        "-i", inputPath,
        "-filter_complex", f"fps={int(fps)},rotate=2*PI*n/{denom}:c=none",
        "-t", str(int(seconds)),
        "-q:v", str(int(q)),
        "-loop", "0",
        "-threads", "0",
        "-an",
        outputPath
    ]
    RunCmd(cmd)

def GetMediaWh(kind, dataBytes=None, filePath=None):
    ext = (kind.extension if kind else "") or ""
    mime = (kind.mime if kind else "") or ""

    if mime.startswith("video") or ext in ("mp4", "mkv", "mov", "webm", "avi"):
        try:
            ffprobe = ffmpegPath().replace("ffmpeg.exe", "ffprobe.exe")
            r = subprocess.run(
                [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", filePath],
                capture_output=True, text=True, check=True
            )
            s = (r.stdout or "").strip()
            if "x" in s:
                w, h = s.split("x", 1)
                return int(w), int(h)
        except:
            return 512, 512

    try:
        if filePath:
            with Image.open(filePath) as im:
                return im.size
        if dataBytes:
            with Image.open(BytesIO(dataBytes)) as im:
                return im.size
    except:
        pass

    return 512, 512

def EnsureMediaCache(this):
    if not hasattr(this, "MediaCache"):
        this.MediaCache = MediaCache()

def MakeStickerKey(imageUrl, xp, spin, sqr, scaleFactor, radiusPercent, maxSize, fps, scale, seconds, q, spinSeconds, spinFps):
    raw = f"{imageUrl}|xp={int(bool(xp))}|spin={int(bool(spin))}|sqr={int(bool(sqr))}|sf={float(scaleFactor or 1.0):.3f}|r={int(radiusPercent)}|ms={int(maxSize)}|fps={int(fps)}|sc={int(scale)}|sec={int(seconds)}|q={int(q)}|ss={int(spinSeconds)}|sfps={int(spinFps)}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

class StickerKind:
    def __init__(self, extension, mime):
        self.extension = extension or "bin"
        self.mime = mime or "application/octet-stream"

def ProjectRoot():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

def GoStickerWorkerSourcePath():
    return os.path.join(ProjectRoot(), "dto", "golang_middle", "sticker_worker.go")

def GoStickerWorkerBinPath():
    name = "sticker_worker.exe" if os.name == "nt" else "sticker_worker"
    return os.path.join(ProjectRoot(), "assets", "cache", name)

def BuildGoStickerWorker():
    if not shutil.which("go"):
        return None

    src = GoStickerWorkerSourcePath()
    if not os.path.isfile(src):
        return None

    out = GoStickerWorkerBinPath()
    os.makedirs(os.path.dirname(out), exist_ok=True)

    try:
        needBuild = (not os.path.exists(out)) or (os.path.getmtime(out) < os.path.getmtime(src))
    except:
        needBuild = True

    if not needBuild:
        return out

    try:
        subprocess.run(
            ["go", "build", "-o", out, src],
            cwd=ProjectRoot(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return out
    except:
        return None

def TryCreateStickerByGo(imageUrl, outputPath, xp=False, maxSize=MaxStickerSize, radiusPercent=0, spin=False, fps=30, scale=480, seconds=30, q=95, spinSeconds=6, spinFps=60, sqr=False, scaleFactor=1.0):
    worker = BuildGoStickerWorker()
    if not worker:
        return None

    cmd = [
        worker,
        "-url", str(imageUrl),
        "-out", str(outputPath),
        "-xp", "true" if bool(xp) else "false",
        "-maxSize", str(int(maxSize)),
        "-radius", str(int(radiusPercent)),
        "-spin", "true" if bool(spin) else "false",
        "-fps", str(int(fps)),
        "-scale", str(int(scale)),
        "-seconds", str(int(seconds)),
        "-q", str(int(q)),
        "-spinSeconds", str(int(spinSeconds)),
        "-spinFps", str(int(spinFps)),
        "-sqr", "true" if bool(sqr) else "false",
        "-scaleFactor", str(float(scaleFactor or 1.0)),
        "-ffmpeg", ffmpegPath(),
        "-webpQuality", str(int(WebpQuality)),
        "-requestTimeout", "12",
        "-commandTimeout", "180"
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if r.returncode != 0:
            return None
        payload = json.loads((r.stdout or "").strip() or "{}")
        return StickerKind(payload.get("extension"), payload.get("mime"))
    except:
        return None

def CreateStickerUrl(imageUrl, outputPath, xp=False, maxSize=MaxStickerSize, radiusPercent=0, spin=False, fps=30, scale=480, seconds=30, q=95, spinSeconds=6, spinFps=60, sqr=False, scaleFactor=1.0):
    goKind = TryCreateStickerByGo(
        imageUrl=imageUrl,
        outputPath=outputPath,
        xp=xp,
        maxSize=maxSize,
        radiusPercent=radiusPercent,
        spin=spin,
        fps=fps,
        scale=scale,
        seconds=seconds,
        q=q,
        spinSeconds=spinSeconds,
        spinFps=spinFps,
        sqr=sqr,
        scaleFactor=scaleFactor
    )
    if goKind:
        return goKind

    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(imageUrl, headers=headers, timeout=12)
    resp.raise_for_status()
    data = resp.content

    kind = filetype.guess(data[:2048])
    if not kind:
        raise Exception("Unsupported file format")

    if kind.extension == "jxl":
        data = ConvertJxlToPngBytes(data)
        kind = filetype.guess(data[:2048])
        if not kind:
            raise Exception("Unsupported file format")

    isGif = kind.extension == "gif"
    isWebp = kind.extension == "webp"
    isVideo = (kind.mime or "").startswith("video")
    isAnimated = isGif or isVideo

    os.makedirs(os.path.dirname(outputPath), exist_ok=True)

    if spin:
        tmpA = tempfile.NamedTemporaryFile(delete=False, suffix=".webp").name
        tmpB = tempfile.NamedTemporaryFile(delete=False, suffix=".webp").name
        try:
            if isAnimated and (not xp) and radiusPercent == 0:
                tmpIn = WriteTmp(data, GuessSuffix(kind))
                try:
                    FfmpegToWebpAnim(tmpIn, tmpA, fps=max(30, int(fps)), scale=int(scale), seconds=int(seconds), q=int(q), sqr=sqr, scaleFactor=scaleFactor)
                finally:
                    try: os.remove(tmpIn)
                    except: pass
            else:
                rp = 0 if sqr else 100
                BytesCreate(data, tmpA, xp=xp, maxSize=maxSize, radiusPercent=rp, isAnimation=isAnimated, sqr=sqr, scaleFactor=scaleFactor)

            if radiusPercent > 0:
                RoundWebpFrames(tmpA, tmpB, radiusPercent)
                SpinWebp(tmpB, outputPath, fps=int(spinFps), seconds=int(spinSeconds), q=min(95, int(q)))
            else:
                SpinWebp(tmpA, outputPath, fps=int(spinFps), seconds=int(spinSeconds), q=min(95, int(q)))
        finally:
            for p in (tmpA, tmpB):
                try: os.remove(p)
                except: pass
        return kind

    if isWebp and (not xp) and radiusPercent == 0 and (not sqr) and float(scaleFactor or 1.0) >= 0.999:
        with open(outputPath, "wb") as f:
            f.write(data)
        return kind

    if isAnimated and (not xp) and radiusPercent == 0:
        tmpIn = WriteTmp(data, GuessSuffix(kind))
        try:
            FfmpegToWebpAnim(tmpIn, outputPath, fps=int(fps), scale=int(scale), seconds=int(seconds), q=int(q), sqr=sqr, scaleFactor=scaleFactor)
        finally:
            try: os.remove(tmpIn)
            except: pass
        return kind

    if isAnimated and (not xp) and radiusPercent > 0:
        tmpIn = WriteTmp(data, GuessSuffix(kind))
        tmpW = tempfile.NamedTemporaryFile(delete=False, suffix=".webp").name
        try:
            FfmpegToWebpAnim(tmpIn, tmpW, fps=int(fps), scale=int(scale), seconds=int(seconds), q=int(q), sqr=sqr, scaleFactor=scaleFactor)
            RoundWebpFrames(tmpW, outputPath, radiusPercent)
        finally:
            for p in (tmpIn, tmpW):
                try: os.remove(p)
                except: pass
        return kind

    if xp and isAnimated:
        raise Exception("xp cho gif/video sẽ rất chậm, chỉ hỗ trợ ảnh tĩnh")

    BytesCreate(data, outputPath, xp=xp, maxSize=maxSize, radiusPercent=radiusPercent, isAnimation=isAnimated, sqr=sqr, scaleFactor=scaleFactor)
    return kind
