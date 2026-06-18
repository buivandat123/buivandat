from functions.services.hook.bot_hook.download_core import *

UrlRe = re.compile(r'https?://\S+', re.I)

def _NowMs():
    return int(time.time() * 1000)

def _ReadDlAutoEnabled(this, threadId):
    settings = ReadServices(this.uid)
    arr = settings.get("dlAuto", [])
    return threadId in arr

def _SetDlAutoEnabled(this, threadId, enabled):
    settings = ReadServices(this.uid)
    arr = settings.setdefault("dlAuto", [])
    if enabled and threadId not in arr:
        arr.append(threadId)
    if not enabled and threadId in arr:
        arr.remove(threadId)
    WriteService(this.uid, settings)
    return enabled

def _ToggleDlAuto(this, threadId):
    return _SetDlAutoEnabled(this, threadId, not _ReadDlAutoEnabled(this, threadId))

def _StartDlParallel(this, data, userId, threadId, type, links, isAudio):
    links = (links or [])[:10]
    if not links:
        return

    def Run():
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = [ex.submit(ProcessSingleLink, i, u, isAudio, threadId, type, this, data, userId) for i, u in enumerate(links)]
            for ft in as_completed(futs):
                try:
                    ft.result()
                except Exception as e:
                    logger.errorMeta(f"Processing error: {e}")

    threading.Thread(target=Run, daemon=True).start()

def HandleDlCommand(this, message, data, userId, threadId, type):
    args = (message.text or "").strip().split()
    if len(args) < 2:
        this.sendMWarning("Give me a url..!", userId, threadId, type)
        return

    if "--auto" in args:
        action = None
        if len(args) >= 3:
            a = args[2].lower()
            if a in ("on", "off"):
                action = a
        if action == "on":
            enabled = _SetDlAutoEnabled(this, threadId, True)
        elif action == "off":
            enabled = _SetDlAutoEnabled(this, threadId, False)
        else:
            enabled = _ToggleDlAuto(this, threadId)

        this.sendMSuccess(f"Auto download is now {'enabled' if enabled else 'disabled'}.", userId, threadId, type)
        return

    isAudio = "-a" in args
    if isAudio:
        args = [x for x in args if x != "-a"]

    links = [x for x in args[1:] if str(x).startswith("http")]
    if not links:
        this.sendMFailed("Invalid URL.", userId, threadId, type)
        return

    _StartDlParallel(this, data, userId, threadId, type, links, isAudio)

def _ToText(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return str(x.get("text") or x.get("content") or "")
    return str(x)

def AutoLink(this, message, data, userId, threadId, type):
    if not _ReadDlAutoEnabled(this, threadId):
        return

    msglink = this.getRecommended(data)
    txt = _ToText(msglink) or _ToText(getattr(message, "text", ""))

    if not txt:
        return

    pfx = getattr(this, "prefix", "") or ""
    if pfx and txt.startswith(pfx):
        return

    links = UrlRe.findall(txt)
    if not links:
        return

    if not hasattr(this, "_DlAutoCooldown"):
        this._DlAutoCooldown = {}

    k = (threadId, userId)
    now = _NowMs()
    last = this._DlAutoCooldown.get(k, 0)
    if now - last < 5000:
        return

    this._DlAutoCooldown[k] = now
    this.sendReaction(data, "/-ok", threadId, type, 10000000)
    _StartDlParallel(this, data, userId, threadId, type, links, False)
    
dependencies = {
    "name": "download",
    "permission": 0,
    "description": "Download Video",
    "cooldown": 5,
    "main": HandleDlCommand
}