from functions.services.hook.bot_hook.webview_core import Shot
from dto.index import *

CACHE_DIR = "assets/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def RunAsync(Coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(Coro)

    Res = {"v": None, "e": None}
    Ev = threading.Event()

    def Runner():
        try:
            Loop = asyncio.new_event_loop()
            asyncio.set_event_loop(Loop)
            Res["v"] = Loop.run_until_complete(Coro)
            Loop.close()
        except Exception as Ex:
            Res["e"] = Ex
        finally:
            Ev.set()

    threading.Thread(target=Runner, daemon=True).start()
    Ev.wait()
    if Res["e"]:
        raise Res["e"]
    return Res["v"]

def PickUrl(text):
    s = (text or "").strip().split()
    for x in s:
        if "://" in x or "." in x:
            return x
    return None

def ToInt(x, d):
    try:
        return int(x)
    except:
        return d

def ToFloat(x, d):
    try:
        return float(x)
    except:
        return d

def GetImageSize(path):
    try:
        with Image.open(path) as im:
            return im.size
    except:
        return None

def screenshotWebsiteCommand(this, message, data, userId, threadId, type):
    text = (message.text or "").strip()
    parts = text.split()
    p = this.prefix
    c = this.rawCommand

    if len(parts) < 2:
        return this.sendMWarning(
            f"Use {p}{c} <url> [--full] [--w 1366] [--h 768] [--wait 1200] [--timeout 30000] [--scale 1] [--fmt png|jpeg|webp]",
            userId, threadId, type
        )

    url = PickUrl(" ".join(parts[1:]))
    if not url:
        return this.sendMWarning("Missing url", userId, threadId, type)

    fullPage = False
    width = 1366
    height = 768
    waitMs = 1200
    timeoutMs = 30000
    scale = 1.0
    fmt = "png"
    quality = 85

    i = 1
    while i < len(parts):
        a = parts[i].lower()
        if a in ("--full", "-f"):
            fullPage = True
            i += 1
            continue
        if a in ("--w", "--width") and i + 1 < len(parts):
            width = ToInt(parts[i + 1], width)
            i += 2
            continue
        if a in ("--h", "--height") and i + 1 < len(parts):
            height = ToInt(parts[i + 1], height)
            i += 2
            continue
        if a in ("--wait", "--waitms") and i + 1 < len(parts):
            waitMs = ToInt(parts[i + 1], waitMs)
            i += 2
            continue
        if a in ("--timeout", "--timeoutms") and i + 1 < len(parts):
            timeoutMs = ToInt(parts[i + 1], timeoutMs)
            i += 2
            continue
        if a in ("--scale", "--dpr") and i + 1 < len(parts):
            scale = ToFloat(parts[i + 1], scale)
            i += 2
            continue
        if a in ("--fmt", "--format") and i + 1 < len(parts):
            fmt = parts[i + 1].lower()
            i += 2
            continue
        if a in ("--q", "--quality") and i + 1 < len(parts):
            quality = ToInt(parts[i + 1], quality)
            i += 2
            continue
        i += 1

    if fmt == "jpg":
        fmt = "jpeg"
    ext = "png" if fmt == "png" else ("webp" if fmt == "webp" else "jpg")
    outPath = os.path.join(CACHE_DIR, f"shot_{int(time.time())}_{uuid.uuid4().hex}.{ext}")

    try:
        RunAsync(Shot(url, outPath, fullPage, width, height, scale, waitMs, timeoutMs, fmt, quality, False))
        size = GetImageSize(outPath)
        w, h = size if size else ("?", "?")
        name = this.userName(userId)
        cap = f"{name}\n{url}"
        this.sendLocalImage(
            outPath, threadId, type,
            message=Message(text=cap, mention=Mention(userId, offset=0, length=len(name))), width=w, height=h
        )
    except Exception as e:
        this.sendMFailed(f"Screenshot failed: {str(e)[:160]}", userId, threadId, type)
    finally:
        try:
            if os.path.exists(outPath):
                os.remove(outPath)
        except:
            pass

dependencies = {
    "name": "screenshot",
    "permission": 0,
    "description": "Screen shot a Website",
    "cooldown": 5,
    "main": screenshotWebsiteCommand
}