from functions.services.hook.bot_hook.sticker_core import *

def StickerCommand(this, message, data, userId, threadId, type):
    cmd = this.prefix + this.rawCommand
    Help = (f"""Quote a attachment to create your custom sticker:
    Args:
        {cmd} nbg: Create no background sticker
        {cmd} sqr: Create square sticker
        {cmd} spin: Create spinning sticker
        {cmd} ai: Send sticker with zSticker AI Mode
        {cmd} [intNumber]: Create radius sticker by the percent on args
    Spec:
        -scale=0.1 - 1: Edit sticker size""")

    if not data.quote:
        return this.sendMWarning(Help, userId, threadId, type)

    attach = json.loads(data.quote.attach)
    imageUrl = attach.get("hdUrl") or attach.get("href")
    if not imageUrl:
        return

    imageUrl = urllib.parse.unquote(imageUrl.replace("\\/", "/"))
    imageUrl = imageUrl.replace("/jxl", "/jpg").replace(".jxl", ".jpg")

    xp = False
    spin = False
    sqr = False
    aiFlag = False
    radiusPercent = 0
    scaleFactor = 1.0
    sqrDefaultR = 20

    fps = 30
    scale = MaxStickerSize
    seconds = 30
    q = 95
    spinFps = 60
    spinSeconds = 6

    for p in (message.text or "").lower().split():
        if p == "nbg":
            xp = True
            continue
        if p == "spin":
            spin = True
            radiusPercent = 100
            continue
        if p == "sqr":
            sqr = True
            continue
        if p == "ai":
            aiFlag = True
            continue
        if p.startswith("-scale=") or p.startswith("scale="):
            try:
                s = p.split("=", 1)[1]
                v = float(s)
                if v > 1.0:
                    v = v / 100.0
                if 0.5 <= v <= 1.0:
                    scaleFactor = v
            except:
                pass
            continue
        if p.isdigit():
            v = int(p)
            if 1 <= v <= 100:
                radiusPercent = v

    if sqr:
        if radiusPercent == 100:
            radiusPercent = 0
        if radiusPercent == 0:
            radiusPercent = sqrDefaultR

    if sqr and radiusPercent == 0:
        radiusPercent = 20

    EnsureMediaCache(this)
    sid = MakeStickerKey(imageUrl, xp, spin, sqr, scaleFactor, radiusPercent, MaxStickerSize, fps, scale, seconds, q, spinSeconds, spinFps)

    cache = this.MediaCache.get(Platf, sid)
    if cache:
        fileUrl = cache.get("fileUrl")
        w = cache.get("w") or 512
        h = cache.get("h") or 512
        if fileUrl and this.MediaCache.isAlive(fileUrl):
            try:
                url = fileUrl + f"?{this.userName(this.uid).replace(' ', '-')}.cachedStk"
                this.sendCustomSticker(
                    staticImgUrl=url,
                    animationImgUrl=url,
                    threadId=threadId,
                    type=type,
                    width=int(w or 512),
                    height=int(h or 512),
                    ttl=3600000,
                    ai=aiFlag
                )
                return
            except:
                this.MediaCache.remove(Platf, sid)

    oriMC = this.sendMCustom("WAITING", "y", "Wait a moment, processing your sticker...", userId, threadId, type)
    outputPath = f"assets/cache/{tsn}_sticker.webp"

    kind = CreateStickerUrl(
        imageUrl, outputPath,
        xp=xp,
        maxSize=MaxStickerSize,
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

    uploadId = this._state.userClientId
    r = this.uploadAttachment(outputPath, uploadId, ThreadType.USER)
    fileUrl = r.get("fileUrl")
    w, h = GetMediaWh(kind, filePath=outputPath)

    if fileUrl:
        this.deleteMessage(oriMC.msgId, this.uid, oriMC.clientId, threadId)
        this.MediaCache.set(Platf, sid, {"url": imageUrl, "xp": xp, "spin": spin, "sqr": sqr, "sf": scaleFactor, "radius": radiusPercent, "w": w, "h": h}, fileUrl)
        url = fileUrl + f"?{this.userName(this.uid).replace(' ', '-')}.zaloStk"
        this.sendCustomSticker(
            staticImgUrl=url,
            animationImgUrl=url,
            threadId=threadId,
            type=type,
            width=int(w or 512),
            height=int(h or 512),
            ttl=3600000,
            ai=aiFlag
        )
        this.sendMSuccess("Here your sticker..!", userId, threadId, type)

    os.remove(outputPath)

dependencies = {
    "name": "sticker",
    "permission": 0,
    "cooldown": 3,
    "description": "Create Sticker",
    "main": StickerCommand
}