from dto.index import *
from src.command.api.music.soundcloud import *

zone = "Asia/Ho_Chi_Minh"
key = "autoSendStatus"
linkvideogirl = [
    "https://fg40.dlfl.vn/329dceed6fcdcf9396dc/1979588035711366033",
    "https://fg43.dlfl.vn/f5e370baf89a58c4018b/2927237803170562106",
    "https://fg41.dlfl.vn/12dab0ef3bcf9b91c2de/1923932897161202007",
    "https://fg43.dlfl.vn/8b405c08d72877762e39/1581562019668632016",
    "https://fg43.dlfl.vn/f1575106da267a782337/1098303575889458287",
    "https://fg40.dlfl.vn/706f14169f363f686627/1713208473411167567",
    "https://fg43.dlfl.vn/42fb5589dea97ef727b8/4298648057908228049",
    "https://fg43.dlfl.vn/e60cea9560b5c0eb99a4/6938669581332504688",
    "https://fg63.dlfl.vn/d8931d06972637786e37/4876382762142020195"
]

linkvideochill = [
    "https://fg41.dlfl.vn/aee9f93c731cd3428a0d/2596453228249502050",
    "https://fg62.dlfl.vn/9201a2d028f088aed1e1/6738389143178356975"
]
schematic = {
    "06:00": [
        {
            "Content": "Ngày mới bắt đầu, chắc sẽ là một ngày bình yên người nhỉ?",
            "Video": "https://fg62.dlfl.vn/820e5a29d00970572918/60199390728100075"
        }
    ],
    "11:00": [
        {
            "Content": "Vẽ hoa vẽ lá vẽ nắng vẽ mây, vẽ luôn vẻ đẹp nàng ấy",
            "Video": "https://fg62.dlfl.vn/752a86610c41ac1ff550/3450114076765375813"
        }
    ],
    "14:00": [
        {
            "Content": "Làm tí nhạc chill nhỉ..",
            "Keywords": ["Nhạc chill", "Lỡ một mai tôi quên tên người", "Giấc mơ"],
            "Send": SoundcloudAutosend
        }
    ],
    "16:00": [
        {
            "Content": "Nạp anh em năng lượng buổi chiều đâyy",
            "Video": "VideoGirl"
        }
    ],
    "18:00": [
        {
            "Content": "Gần bữa tối rồi, ngắm tí vitamin gái ăn cơm cho nó ngon hầy",
            "Video": "VideoGirl"
        }
    ],
    "19:00": [
        {
            "Content": "Tận hưởng những giây phút của bản thân..!",
            "Video": "https://fg41.dlfl.vn/6ca5d479a15a0104584b/5971004858182776734"
        }
    ],
    "21:00": [
        {
            "Content": "Giờ này lạnh lắm, nếu có ra đường nhớ mang áo ấm nhé",
            "Keywords": ["Gió", "Ấm"],
            "Send": SoundcloudAutosend
        }
    ],
    "22:00": [
        {
            "Content": "Khuya rồi đó, chúc bạn ngủ ngon nhé. Ngủ đi",
            "Video": "VideoGirl"
        }
    ],
    "23:00": [
        {
            "Content": "Tận hưởng chút nhạc buổi khuya nhé!",
            "Keywords": ["B Ray", "25", "Đen vâu"],
            "Send": SoundcloudAutosend
        }
    ],
    "00:00": [
        {
            "Content": "Cuộc đời bình yên, ta tưởng rằng vậy là ta đã trường thành nhưng sau rồi ta lại ngây ngô vì cô gái ấy",
            "Video": "https://fg40.dlfl.vn/adf5c5134f33ef6db622/3659112734766094094"
        }
    ],
    "01:00": [
        {
            "Content": "Em đi rồi, anh cũng không biết phải làm sao..",
            "Video": "https://fg43.dlfl.vn/38b4babe309e90c0c98f/3125405985925627006"
        }
    ]
}

def validHHMM(value):
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{2}:\d{2}", text):
        return False
    hh, mm = text.split(":", 1)
    try:
        h, m = int(hh), int(mm)
        return 0 <= h <= 23 and 0 <= m <= 59
    except:
        return False

def normalizeScheduler(raw):
    src = raw if isinstance(raw, dict) and raw else schematic
    out = {}
    for t, msg in src.items():
        hhmm = str(t or "").strip()
        if validHHMM(hhmm) and isinstance(msg, (str, dict, list)) and msg:
            out[hhmm] = msg
    return out or dict(schematic)

def ffmpegPath():
    try:
        return (databaseReader() or {}).get("ffmpegPath") or "ffmpeg"
    except:
        return "ffmpeg"

def ffprobePath():
    path = str(ffmpegPath())
    if path.endswith("ffmpeg.exe"):
        return path.replace("ffmpeg.exe", "ffprobe.exe")
    if path.endswith("ffmpeg"):
        return path[:-6] + "ffprobe"
    return "ffprobe"

def downloadVideo(url, timeout=90):
    url = str(url or "").strip()
    if not url:
        return ""

    resp = requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    fd, path = tempfile.mkstemp(prefix="autosend-", suffix=".mp4")
    os.close(fd)

    with open(path, "wb") as f:
        for chunk in resp.iter_content(65536):
            if chunk:
                f.write(chunk)

    return path

def probeVideoMeta(videoPath):
    try:
        out = subprocess.check_output(
            [
                ffprobePath(),
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration:format=duration",
                "-of", "json",
                videoPath
            ],
            stderr=subprocess.STDOUT
        )
        data = json.loads((out or b"").decode("utf-8", "ignore") or "{}")
        stream = (data.get("streams") or [{}])[0] or {}
        fmt = data.get("format") or {}

        width = int(float(stream.get("width") or 0) or 0) or 1280
        height = int(float(stream.get("height") or 0) or 0) or 720
        duration = stream.get("duration")
        if duration is None:
            duration = fmt.get("duration")

        return width, height, max(int(float(duration or 0) * 1000), 0)
    except:
        return 1280, 720, 0

def makeVideoThumb(videoPath, width, height):
    fd, out = tempfile.mkstemp(prefix="autosend-thumb-", suffix=".jpg")
    os.close(fd)

    subprocess.run(
        [
            ffmpegPath(),
            "-y",
            "-ss", "0.5",
            "-i", videoPath,
            "-vframes", "1",
            "-vf", f"scale={int(width)}:{int(height)}:force_original_aspect_ratio=decrease",
            out
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out

    try:
        os.remove(out)
    except:
        pass
    return ""

def extractUrl(uploaded):
    if isinstance(uploaded, str):
        return uploaded.strip()

    if isinstance(uploaded, dict):
        for k in ("fileUrl", "hdUrl", "href", "url", "downloadUrl", "originUrl"):
            v = uploaded.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()

    return ""

def sendVideoByUpload(this, threadId, type, videoUrl, contentText=""):
    videoPath = ""
    thumbPath = ""

    try:
        videoPath = downloadVideo(videoUrl)
        if not videoPath:
            return False

        width, height, duration = probeVideoMeta(videoPath)
        thumbPath = makeVideoThumb(videoPath, width, height)

        uploadedVideo = extractUrl(this.uploadAttachment(videoPath, threadId, type))
        if not uploadedVideo:
            return False

        thumbUrl = ""
        if thumbPath:
            try:
                thumbUrl = extractUrl(this.uploadImage(thumbPath, threadId, type))
            except:
                thumbUrl = extractUrl(this.uploadAttachment(thumbPath, threadId, type))

        this.sendVideo(
            videoUrl=uploadedVideo,
            thumbnailUrl=thumbUrl,
            duration=duration,
            threadId=threadId,
            type=type,
            width=width,
            height=height,
            message=Message(text=str(contentText or ""))
        )
        return True
    except Exception as e:
        logger.errorMeta(f"Auto send video failed {threadId}: {e}")
        return False
    finally:
        for path in (thumbPath, videoPath):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

def formatTimedContent(content, nowText=None):
    text = str(content or "").strip()
    if not text:
        return ""

    if not nowText:
        nowText = datetime.now(pytz.timezone(zone)).strftime("%H:%M")
    return f"> {nowText} <\n\n{text}"

def resolveVideos(videos):
    vals = videos if isinstance(videos, list) else [videos]
    out = []
    pool = [str(x).strip() for x in (linkvideogirl or []) if str(x or "").strip()]

    for val in vals:
        text = str(val or "").strip()
        if not text:
            continue

        if re.match(r"^https?://", text, flags=re.IGNORECASE):
            out.append(text)
            continue

        if pool:
            out.append(random.choice(pool))

    return out

def sendScheduledContent(this, threadId, type, content):
    if isinstance(content, list):
        items = [x for x in content if isinstance(x, (str, dict))]
    elif isinstance(content, (str, dict)):
        items = [content]
    else:
        items = []

    nowText = datetime.now(pytz.timezone(zone)).strftime("%H:%M")
    sent = False

    for item in items:
        if isinstance(item, str):
            text = formatTimedContent(item, nowText)
            if text:
                this.sendMention(text, None, threadId, type)
                sent = True
            continue

        text = str(item.get("Content") or item.get("content") or "").strip()
        sender = item.get("Send") or item.get("send")

        if callable(sender):
            try:
                if sender(this, threadId, type, text, item):
                    sent = True
            except Exception as e:
                logger.errorMeta(f"Auto send callback failed {threadId}: {e}")
            continue

        videos = item.get("Video") or item.get("video") or []

        if isinstance(videos, str):
            videos = [videos.strip()] if videos.strip() else []
        elif isinstance(videos, list):
            videos = [str(x).strip() for x in videos if str(x).strip()]
        else:
            videos = []

        videos = resolveVideos(videos)

        if videos:
            sendText = formatTimedContent(text, nowText)
            for i, video in enumerate(videos):
                if sendVideoByUpload(this, threadId, type, video, sendText if i == 0 else ""):
                    sent = True
            continue

        text = formatTimedContent(text, nowText)
        if text:
            this.sendMention(text, None, threadId, type)
            sent = True

    return sent

def getSendState(uid):
    services = ReadServices(uid) or {}
    state = dict(services.get(key) or {})
    threads = [str(x).strip() for x in state.get("threads") or [] if str(x or "").strip()]
    scheduler = normalizeScheduler(schematic)
    lastSent = dict(state.get("lastSent") or {})
    return services, state, threads, scheduler, lastSent

def saveSendState(uid, services, state, threads, lastSent):
    state["threads"] = [str(x).strip() for x in threads or [] if str(x or "").strip()]
    state["lastSent"] = dict(lastSent or {})
    services[key] = state
    WriteService(uid, services)

def schedulerHandle(this):
    services, state, threads, scheduler, lastSent = getSendState(this.uid)
    if not threads or not scheduler:
        return

    now = datetime.now(pytz.timezone(zone))
    hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    content = scheduler.get(hhmm)
    if not content:
        return

    changed = False

    for threadId in threads:
        sentKey = f"{threadId}|{today}|{hhmm}"
        if sentKey in lastSent:
            continue

        try:
            if sendScheduledContent(this, threadId, ThreadType.GROUP, content):
                lastSent[sentKey] = int(time.time())
                changed = True
        except Exception as e:
            logger.errorMeta(f"Auto send failed {threadId}: {e}")

    if not changed:
        return

    lastSent = {k: v for k, v in lastSent.items() if f"|{today}|" in str(k)}
    saveSendState(this.uid, services, state, threads, lastSent)

def initSchedulerHandle(this):
    if getattr(this, "autoSendLoop", False):
        return

    this.autoSendLoop = True

    def loop():
        while True:
            try:
                schedulerHandle(this)
            except Exception as e:
                logger.errorMeta(f"Scheduler loop error: {e}")
            time.sleep(15)

    threading.Thread(target=loop, daemon=True).start()
