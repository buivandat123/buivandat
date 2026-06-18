from dto.index import *

def isAllMode(groups):
    return isinstance(groups, list) and len(groups) == 1 and groups[0] == -1

def getAllGroups(this):
    grid = this.fetchAllGroups().get("gridVerMap", {})
    if hasattr(grid, "items") and not isinstance(grid, dict):
        grid = dict(grid)
    return [str(gid) for gid in grid.keys()]

def guessExt(url, contentType=""):
    path = (urlparse(url or "").path or "")
    ext = os.path.splitext(path)[1].lower()
    if ext and len(ext) <= 8:
        return ext

    ct = (contentType or "").split(";")[0].strip().lower()
    if ct:
        mapped = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "video/x-matroska": ".mkv",
            "video/webm": ".webm",
            "application/pdf": ".pdf",
        }.get(ct)
        if mapped:
            return mapped
        ext2 = mimetypes.guess_extension(ct) or ""
        if ext2:
            return ext2
    return ".bin"

def downloadFile(url, timeout=30):
    url = (url or "").strip()
    if not url:
        return "", "", b""

    if requests:
        r = requests.get(url, timeout=timeout, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "") or ""
        data = r.content
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ct = resp.headers.get("Content-Type", "") or ""
            data = resp.read()

    if not data:
        return "", "", b""

    fd, path = tempfile.mkstemp(prefix="pr-", suffix=guessExt(url, ct))
    os.close(fd)
    with open(path, "wb") as f:
        f.write(data)
    return path, ct, data

def imageWhFromBytes(dataBytes):
    if not Image or not dataBytes:
        return 1280, 720
    try:
        from io import BytesIO
        with Image.open(BytesIO(dataBytes)) as im:
            return int(im.size[0]), int(im.size[1])
    except:
        return 1280, 720

def ffmpegPath():
    try:
        from functions.engine.data.data import databaseReader
        return (databaseReader() or {}).get("ffmpegPath") or "ffmpeg"
    except:
        return "ffmpeg"

def ffprobePath():
    fp = ffmpegPath()
    if fp.endswith("ffmpeg.exe"):
        return fp.replace("ffmpeg.exe", "ffprobe.exe")
    if fp.endswith("ffmpeg"):
        return fp[:-6] + "ffprobe"
    return "ffprobe"

def getVideoMeta(filePath):
    try:
        r = subprocess.run(
            [
                ffprobePath(),
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height:format=duration",
                "-of", "json",
                filePath,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        d = json.loads((r.stdout or "").strip() or "{}")
        st = (d.get("streams") or [{}])[0] or {}
        fm = d.get("format") or {}
        return int(st.get("width") or 1280), int(st.get("height") or 720), int(float(fm.get("duration") or 0))
    except:
        return 1280, 720, 0

def makeVideoThumb(filePath, width=1280, height=720):
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
    vf = f"scale={int(width)}:{int(height)}:force_original_aspect_ratio=decrease"
    subprocess.run(
        [ffmpegPath(), "-y", "-ss", "0.5", "-i", filePath, "-vframes", "1", "-vf", vf, out],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    try:
        os.remove(out)
    except:
        pass
    return ""

def uploadThumb(this, thumbPath, threadId, type):
    if not thumbPath:
        return ""
    try:
        res = this.uploadImage(thumbPath, threadId, type)
    finally:
        try:
            os.remove(thumbPath)
        except:
            pass

    if isinstance(res, str):
        return res.strip()
    if isinstance(res, dict):
        for k in ("href", "url", "downloadUrl", "fileUrl", "hdUrl"):
            v = res.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""

def normalizePrContent(v):
    if isinstance(v, dict):
        ctx = (v.get("context") or "").strip()
        imgs = v.get("imageAttachment")
        vids = v.get("videoAttachment")
        if isinstance(imgs, str):
            imgs = [imgs] if imgs.strip() else []
        elif not isinstance(imgs, list):
            imgs = []
        if isinstance(vids, str):
            vids = [vids] if vids.strip() else []
        elif not isinstance(vids, list):
            vids = []
        return {
            "context": ctx,
            "imageAttachment": [str(x).strip() for x in imgs if str(x).strip()],
            "videoAttachment": [str(x).strip() for x in vids if str(x).strip()],
        }
    return {"context": (v or "").strip(), "imageAttachment": [], "videoAttachment": []}

def extractUrls(attach):
    if isinstance(attach, str):
        try:
            attach = json.loads(attach) if attach else {}
        except:
            attach = {"href": attach}

    if not isinstance(attach, dict):
        return [], attach

    urls = []
    for k in ("href", "hdUrl", "url", "originUrl", "downloadUrl", "fileUrl"):
        v = attach.get(k)
        if isinstance(v, str) and v.strip().startswith("http"):
            urls.append(v.strip())

    items = attach.get("items") or attach.get("data") or attach.get("medias") or attach.get("list")
    if isinstance(items, list):
        for it in items:
            if isinstance(it, str) and it.strip().startswith("http"):
                urls.append(it.strip())
            elif isinstance(it, dict):
                for k in ("href", "hdUrl", "url", "originUrl", "downloadUrl", "fileUrl"):
                    v = it.get(k)
                    if isinstance(v, str) and v.strip().startswith("http"):
                        urls.append(v.strip())

    return list(dict.fromkeys(urls)), attach

def parseTimes(parts, startIndex):
    raw = " ".join(parts[startIndex:]).strip()
    if not raw:
        return []
    raw = raw.replace(";", ",").replace("|", ",")
    seen = set()
    out = []
    for chunk in raw.split(","):
        for t in chunk.strip().split():
            if ":" not in t:
                continue
            hh, mm = t.split(":", 1)
            if not (hh.isdigit() and mm.isdigit()):
                continue
            h = int(hh)
            m = int(mm)
            if 0 <= h <= 23 and 0 <= m <= 59:
                s = f"{h:02d}:{m:02d}"
                if s not in seen:
                    seen.add(s)
                    out.append(s)
    return out

def shouldFireNow(this, timesList):
    if not timesList:
        return False
    now = datetime.now()
    hm = now.strftime("%H:%M")
    if hm not in timesList:
        return False
    key = now.strftime("%Y%m%d") + "|" + hm
    if getattr(this, "prLastTick", "") == key:
        return False
    this.prLastTick = key
    return True

def sendVideoWithMeta(this, videoUrl, threadId, type):
    videoPath, _, _ = downloadFile(videoUrl)
    if not videoPath:
        return
    try:
        w, h, dur = getVideoMeta(videoPath)
        thumbUrl = uploadThumb(this, makeVideoThumb(videoPath, w, h), threadId, type)
        this.sendVideo(this, videoUrl, thumbUrl, int(dur), threadId, type, width=int(w), height=int(h))
    finally:
        try:
            os.remove(videoPath)
        except:
            pass

def sendPrContent(this, threadId, type, content=None):
    content = normalizePrContent(content)
    ctx = content.get("context") or "..."
    imgs = content.get("imageAttachment") or []
    vids = content.get("videoAttachment") or []

    this.sendMMessage(ctx, None, threadId, type)
    time.sleep(0.25)

    if imgs:
        _, _, b = downloadFile(imgs[0])
        w, h = imageWhFromBytes(b)
        if len(imgs) == 1:
            this.sendImage(imgs[0], threadId, type, int(w), int(h))
        else:
            this.sendMultiImage(imgs, threadId, type, int(w), int(h))
        time.sleep(0.25)

    for vurl in vids:
        sendVideoWithMeta(this, vurl, threadId, type)
        time.sleep(0.25)

def prOnce(this, gids):
    content = normalizePrContent((ReadServices(this.uid) or {}).get("prContent"))
    for gid in gids:
        try:
            sendPrContent(this, gid, ThreadType.GROUP, content)
        except Exception as e:
            logger.error(f"PR error gid={gid}: {e}")

def prWorker(this):
    while True:
        pr = ReadServices(this.uid) or {}
        if not pr.get("prAuto", False):
            break

        groups = pr.get("prGroups", [])
        gids = getAllGroups(this) if isAllMode(groups) else [str(g) for g in groups if g != -1]
        timesList = pr.get("prTimes")
        if isinstance(timesList, str):
            timesList = [timesList]
        timesList = [str(x).strip() for x in timesList if str(x).strip()] if isinstance(timesList, list) else []

        if timesList:
            if gids and shouldFireNow(this, timesList):
                prOnce(this, gids)
            time.sleep(1)
        else:
            if gids:
                prOnce(this, gids)
            time.sleep(30)

def startPR(this):
    t = getattr(this, "prThread", None)
    if t and t.is_alive():
        return
    this.prThread = threading.Thread(target=prWorker, args=(this,), daemon=True)
    this.prThread.start()

def initPR(this):
    pr = ReadServices(this.uid) or {}
    groups = pr.get("prGroups", [])
    gids = getAllGroups(this) if (isAllMode(groups) or not groups) else [str(g) for g in groups if g != -1]
    if gids:
        prOnce(this, gids)

def uniqMerge(baseList, addList):
    seen = set()
    out = []
    for x in (baseList if isinstance(baseList, list) else []) + (addList if isinstance(addList, list) else []):
        s = str(x).strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def buildPrContentFromQuote(this, data, fallbackText=""):
    q = getattr(data, "quote", None)
    out = {"context": (fallbackText or "").strip(), "videoAttachment": [], "imageAttachment": []}
    if not q:
        return out

    mt = getattr(q, "cliMsgType", None)
    if mt == 1:
        out["context"] = (getattr(q, "msg", "") or "").strip() or out["context"]
        return out

    urls, attach = extractUrls(getattr(q, "attach", None))
    if not urls:
        return out

    isVideo = (mt == 44) or bool(isinstance(attach, dict) and (attach.get("duration") or attach.get("video") or attach.get("isVideo")))
    out["videoAttachment" if isVideo else "imageAttachment"] = urls
    return out

def prDetailText(pr):
    content = normalizePrContent(pr.get("prContent"))
    lines = [f"Content: {content.get('context') or '(empty)'}"]
    if content.get("videoAttachment"):
        lines.append("Video:")
        for i, u in enumerate(content["videoAttachment"], 1):
            lines.append(f"{i}. {u}")
    if content.get("imageAttachment"):
        lines.append("Images:")
        for i, u in enumerate(content["imageAttachment"], 1):
            lines.append(f"{i}. {u}")

    timesList = pr.get("prTimes")
    if isinstance(timesList, str):
        timesList = [timesList]
    timesList = [str(x).strip() for x in timesList if str(x).strip()] if isinstance(timesList, list) else []

    lines.append("")
    lines.append("Time: " + (", ".join(sorted(set(timesList))) if timesList else "None"))
    lines.append(f"Status: {bool(pr.get('prAuto', False))}")
    return "\n".join(lines)

def prCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    c = this.prefix + this.rawCommand
    prHelp = f"""
Noooooo
""".strip()

    if len(parts) < 2:
        return this.sendMWarning(prHelp, userId, threadId, type)

    action = parts[1].lower()
    pr = ReadServices(this.uid) or {}
    pr.setdefault("prGroups", [])
    tid = str(threadId)

    if action == "help":
        return this.sendMWarning(prHelp, userId, threadId, type)

    if action == "start":
        pr["prAuto"] = True
        WriteService(this.uid, pr)
        startPR(this)
        return this.sendMSuccess("PR started", userId, threadId, type)

    if action == "stop":
        pr["prAuto"] = False
        WriteService(this.uid, pr)
        return this.sendMSuccess("PR stopped", userId, threadId, type)

    if action == "init":
        initPR(this)
        return this.sendMSuccess("PR init done", userId, threadId, type)

    if action == "preview":
        content = normalizePrContent(pr.get("prContent"))
        if not content.get("context") and not content.get("imageAttachment") and not content.get("videoAttachment"):
            return this.sendMWarning("Empty content", userId, threadId, type)
        try:
            sendPrContent(this, threadId, type, content)
            return this.sendMSuccess("PR preview done", userId, threadId, type)
        except Exception as e:
            return this.sendMFailed(e, userId, threadId, type)

    if action == "detail":
        return this.sendMSuccess(prDetailText(pr), userId, threadId, type)

    if action == "time":
        if len(parts) < 3:
            return this.sendMWarning(prHelp, userId, threadId, type)

        sub = parts[2].lower()
        timesList = pr.get("prTimes")
        if isinstance(timesList, str):
            timesList = [timesList]
        timesList = [str(x).strip() for x in timesList if str(x).strip()] if isinstance(timesList, list) else []

        if sub == "list":
            return this.sendMSuccess("\n".join(sorted(set(timesList))) if timesList else "No times", userId, threadId, type)

        items = parseTimes(parts, 3)
        if not items:
            return this.sendMWarning("No valid time", userId, threadId, type)

        s = set(timesList)
        if sub == "add":
            s.update(items)
            pr["prTimes"] = sorted(s)
            WriteService(this.uid, pr)
            return this.sendMSuccess("Added: " + ", ".join(items), userId, threadId, type)

        if sub == "rm":
            removed = [t for t in items if t in s]
            for t in removed:
                s.remove(t)
            pr["prTimes"] = sorted(s)
            WriteService(this.uid, pr)
            return this.sendMSuccess("Removed: " + (", ".join(removed) if removed else "None"), userId, threadId, type)

        return this.sendMWarning(prHelp, userId, threadId, type)

    if action == "add":
        if len(parts) >= 3 and parts[2].lower() == "all":
            pr["prGroups"] = [-1]
            WriteService(this.uid, pr)
            return this.sendMSuccess("PR set to all groups", userId, threadId, type)

        if -1 in pr["prGroups"]:
            return this.sendMWarning("PR is in all mode", userId, threadId, type)

        if tid not in pr["prGroups"]:
            pr["prGroups"].append(tid)
            WriteService(this.uid, pr)
        return this.sendMSuccess("Added PR group", userId, threadId, type)

    if action == "remove":
        if len(parts) >= 3 and parts[2].lower() == "all":
            pr["prGroups"] = []
            WriteService(this.uid, pr)
            return this.sendMSuccess("Removed all groups", userId, threadId, type)

        if tid in pr["prGroups"]:
            pr["prGroups"].remove(tid)
            WriteService(this.uid, pr)
        return this.sendMSuccess("Removed PR group", userId, threadId, type)

    if action == "set":
        try:
            sub = parts[2].lower() if len(parts) >= 3 else ""
            cur = normalizePrContent(pr.get("prContent"))

            if sub == "reset":
                pr["prContent"] = {"context": "", "videoAttachment": [], "imageAttachment": []}
                WriteService(this.uid, pr)
                return this.sendMSuccess("PR content reset", userId, threadId, type)

            if sub == "rm" and len(parts) >= 5:
                kind = parts[3].lower()
                arg = parts[4].lower()
                if kind not in ("video", "image"):
                    return this.sendMWarning("Use: set rm video|image ...", userId, threadId, type)

                key = "videoAttachment" if kind == "video" else "imageAttachment"
                arr = cur.get(key) or []

                if arg == "all":
                    cur[key] = []
                    pr["prContent"] = cur
                    WriteService(this.uid, pr)
                    return this.sendMSuccess(f"Cleared {kind}", userId, threadId, type)

                if not arg.isdigit():
                    return this.sendMWarning("Invalid index", userId, threadId, type)

                idx = int(arg)
                if idx <= 0 or idx > len(arr):
                    return this.sendMWarning("Index out of range", userId, threadId, type)

                arr.pop(idx - 1)
                cur[key] = arr
                pr["prContent"] = cur
                WriteService(this.uid, pr)
                return this.sendMSuccess(f"Removed {kind} #{idx}", userId, threadId, type)

            neu = buildPrContentFromQuote(this, data, " ".join(parts[2:]).strip())
            if neu.get("context"):
                cur["context"] = neu["context"]
            if neu.get("imageAttachment"):
                cur["imageAttachment"] = uniqMerge(cur.get("imageAttachment"), neu.get("imageAttachment"))
            if neu.get("videoAttachment"):
                cur["videoAttachment"] = uniqMerge(cur.get("videoAttachment"), neu.get("videoAttachment"))

            if not cur.get("context") and not cur.get("imageAttachment") and not cur.get("videoAttachment"):
                return this.sendMWarning("Empty content", userId, threadId, type)

            pr["prContent"] = cur
            WriteService(this.uid, pr)
            return this.sendMSuccess("PR content saved", userId, threadId, type)
        except Exception as e:
            return this.sendMFailed(e, userId, threadId, type)

    return this.sendMWarning(prHelp, userId, threadId, type)

dependencies = {
    "name": "pr",
    "permission": 3,
    "cooldown": 2,
    "description": "PR auto accept group invite",
    "main": prCommand
}