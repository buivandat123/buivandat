from ....index import *
class SendApi:
    def _IsUrl(this, v):
        if not v:
            return False
        s = str(v).strip().lower()
        return s.startswith("http://") or s.startswith("https://")

    def _NormThreadId(this, threadId):
        try:
            return str(int(threadId) or int(this.uid))
        except:
            return str(threadId or this.uid)

    def _GetExt(this, p):
        s = str(p or "").split("?")[0].split("#")[0]
        i = s.rfind(".")
        return s[i + 1 :].lower() if i != -1 and i + 1 < len(s) else ""

    def _GetFileName(this, p, fallback="default"):
        s = str(p or "").split("?")[0].split("#")[0]
        b = os.path.basename(s)
        return b if b else fallback

    def _GetLocalSize(this, p):
        try:
            return int(os.stat(p).st_size)
        except:
            return 0

    def _GetImageWhLocal(this, p):
        try:
            from PIL import Image
            with Image.open(p) as im:
                w, h = im.size
            return int(w), int(h)
        except:
            return 2560, 2560

    def _GetImageWhRemote(this, url, timeout=20):
        try:
            import requests
            from PIL import Image
            from io import BytesIO
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            with Image.open(BytesIO(r.content)) as im:
                w, h = im.size
            return int(w), int(h)
        except:
            return 2560, 2560

    def _GetSystemFfmpegPath(this):
        import shutil
        cands = ["ffmpeg", "ffmpeg.exe"]
        for c in cands:
            fp = shutil.which(c)
            if fp:
                return fp
        return "ffmpeg"

    def _ProbeVideo(this, p):
        try:
            from functions.services.hook.bot_hook.download_core import GetFfprobePath
            import subprocess, json as _json, shutil

            ffprobe = GetFfprobePath(this._GetSystemFfmpegPath())
            if not ffprobe:
                ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe") or "ffprobe"

            out = subprocess.check_output([
                ffprobe, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "json",
                p
            ], stderr=subprocess.STDOUT)
            j = _json.loads(out.decode("utf-8", "ignore") or "{}")
            st = (j.get("streams") or [{}])[0]
            w = int(float(st.get("width") or 0) or 0)
            h = int(float(st.get("height") or 0) or 0)
            d = st.get("duration")
            dur = int(float(d) * 1000) if d is not None else 0
            return (w or 1080), (h or 1920), (dur or 0)
        except:
            return 1080, 1920, 0

    def _TempPath(this, ext="bin"):
        os.makedirs("assets/cache", exist_ok=True)
        return os.path.join("assets/cache", f"{int(utils.now()*1000)}.{ext}")

    def _DownloadTo(this, url, dst, timeout=60):
        import requests
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        with open(dst, "wb") as f:
            for c in r.iter_content(chunk_size=65536):
                if c:
                    f.write(c)
        return dst

    def _ParseStd(this, data, type, clientId=None):
        if data.get("error_code") == 0:
            results = data.get("data")
            if not results:
                raise ZaloAPIException("Error #1337 when sending requests: Data is None")
            results = this._decode(results)
            results = results.get("data") or results
            if isinstance(results, dict):
                if clientId is not None:
                    results["clientId"] = clientId
            elif isinstance(results, str):
                try:
                    results = json.loads(results)
                    if clientId is not None:
                        results["clientId"] = clientId
                except Exception:
                    raise ZaloAPIException(f"Error #1337 when sending requests: {results}")
            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)
        raise ZaloAPIException(f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}")

    def _BuildSendMessage(this, message, threadId, type, mark_message=None, ttl=0, clientId=None):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }
        clientId = clientId or utils.now()
        payloadParams = { "message": message.text, "clientId": clientId, "imei": this._imei, "ttl": ttl }

        mm = str(mark_message or "").lower()
        if mm in ("important", "urgent"):
            payloadParams["metaData"] = { "urgency": 1 if mm == "important" else 2 }

        if getattr(message, "style", None):
            payloadParams["textProperties"] = message.style

        if type == ThreadType.USER:
            url = "https://tt-chat2-wpa.chat.zalo.me/api/message/sms"
            payloadParams["toid"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/sendmsg"
            payloadParams["visibility"] = 0
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, clientId

    def _SendMessageCore(this, message, threadId, type, mark_message=None, ttl=0, clientId=None, injectMention=False):
        threadId = this._NormThreadId(threadId)
        url, params, payload, cli = this._BuildSendMessage(message, threadId, type, mark_message, ttl, clientId)
        if injectMention and getattr(message, "mention", None):
            decoded = this._decode(payload["params"])
            decoded["mentionInfo"] = message.mention
            payload["params"] = this._encode(decoded)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._ParseStd(data, type, cli)

    async def _SendMessageCoreAsync(this, message, threadId, type, mark_message=None, ttl=0, clientId=None, injectMention=False):
        threadId = this._NormThreadId(threadId)
        url, params, payload, cli = this._BuildSendMessage(message, threadId, type, mark_message, ttl, clientId)
        if injectMention and getattr(message, "mention", None):
            decoded = this._decode(payload["params"])
            decoded["mentionInfo"] = message.mention
            payload["params"] = this._encode(decoded)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._ParseStd(data, type, cli)

    def sendMessage(this, message, threadId, type, mark_message=None, ttl=0):
        return this._SendMessageCore(message, threadId, type, mark_message, ttl, None, False)

    async def sendMessageAsync(this, message, threadId, type, mark_message=None, ttl=0):
        return await this._SendMessageCoreAsync(message, threadId, type, mark_message, ttl, None, False)

    def sendMessageByCliMsgId(this, message, threadId, type, clientId=None, mark_message=None, ttl=0):
        return this._SendMessageCore(message, threadId, type, mark_message, ttl, clientId, True)

    async def sendMessageByCliMsgIdAsync(this, message, threadId, type, clientId=None, mark_message=None, ttl=0):
        return await this._SendMessageCoreAsync(message, threadId, type, mark_message, ttl, clientId, True)

    def _BuildReplyMessage(this, message, replyMsg, threadId, type, ttl=0):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }
        clientId = utils.now()

        payloadParams = {
            "message": message.text,
            "clientId": clientId,
            "qmsgOwner": str(int(replyMsg.uidFrom) or this.uid),
            "qmsgId": replyMsg.msgId,
            "qmsgCliId": replyMsg.cliMsgId,
            "qmsgType": utils.getClientMessageType(replyMsg.msgType),
            "qmsg": replyMsg.content,
            "qmsgTs": replyMsg.ts,
            "qmsgAttach": json.dumps({}),
            "qmsgTTL": 0,
            "ttl": ttl
        }

        if not isinstance(replyMsg.content, str):
            payloadParams["qmsg"] = ""
            payloadParams["qmsgAttach"] = json.dumps(replyMsg.content.toDict())

        if getattr(message, "style", None):
            payloadParams["textProperties"] = message.style

        if getattr(message, "mention", None):
            payloadParams["mentionInfo"] = message.mention

        if type == ThreadType.USER:
            url = "https://tt-chat2-wpa.chat.zalo.me/api/message/quote"
            payloadParams["toid"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/quote"
            payloadParams["visibility"] = 0
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, clientId

    def replyMessage(this, message, replyMsg, threadId, type, ttl=0):
        threadId = this._NormThreadId(threadId)
        url, params, payload, clientId = this._BuildReplyMessage(message, replyMsg, threadId, type, ttl)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._ParseStd(data, type, clientId)

    async def replyMessageAsync(this, message, replyMsg, threadId, type, ttl=0):
        threadId = this._NormThreadId(threadId)
        url, params, payload, clientId = this._BuildReplyMessage(message, replyMsg, threadId, type, ttl)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._ParseStd(data, type, clientId)

    def _BuildSendMention(this, message, groupId, ttl=0):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }
        clientId = utils.now()

        payloadParams = {
            "grid": str(groupId),
            "message": message.text,
            "mentionInfo": message.mention,
            "clientId": clientId,
            "visibility": 0,
            "ttl": ttl
        }

        if getattr(message, "style", None):
            payloadParams["textProperties"] = message.style

        payload = { "params": this._encode(payloadParams) }
        url = "https://tt-group-wpa.chat.zalo.me/api/group/mention"
        return url, params, payload, clientId

    def sendMentimessageListener(this, message, groupId, ttl=0):
        url, params, payload, clientId = this._BuildSendMention(message, groupId, ttl)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._ParseStd(data, ThreadType.GROUP, clientId)

    async def sendMentimessageListenerAsync(this, message, groupId, ttl=0):
        url, params, payload, clientId = this._BuildSendMention(message, groupId, ttl)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._ParseStd(data, ThreadType.GROUP, clientId)

    def _SendTextCore(this, message, threadId, type, mark_message=None, ttl=0):
        threadId = this._NormThreadId(threadId)
        if getattr(message, "mention", None):
            return this.sendMentimessageListener(message, threadId, ttl)
        return this.sendMessage(message, threadId, type, mark_message, ttl)

    async def _SendTextCoreAsync(this, message, threadId, type, mark_message=None, ttl=0):
        threadId = this._NormThreadId(threadId)
        if getattr(message, "mention", None):
            return await this.sendMentimessageListenerAsync(message, threadId, ttl)
        return await this.sendMessageAsync(message, threadId, type, mark_message, ttl)

    def _SendLinkAuto(this, linkUrl, threadId, type, message=None, ttl=0):
        try:
            return this.sendLink(linkUrl, threadId, type, message, ttl)
        except TypeError:
            return this.sendLink(
                linkUrl=linkUrl,
                title="",
                threadId=threadId,
                type=type,
                thumbnailUrl=None,
                domainUrl=None,
                desc=None,
                message=message,
                ttl=ttl
            )

    async def _SendLinkAutoAsync(this, linkUrl, threadId, type, message=None, ttl=0):
        return await asyncio.to_thread(this._SendLinkAuto, linkUrl, threadId, type, message, ttl)

    def _RunCoro(this, coro):
        try:
            asyncio.get_running_loop()
            return asyncio.run(asyncio.to_thread(lambda: asyncio.run(coro)))
        except RuntimeError:
            return asyncio.run(coro)

    def _SendAttachmentCoreImpl(this, message, attachment, threadId, type, ttl=0, isAsync=False, **kwargs):
        threadId = this._NormThreadId(threadId)
        isUrl = this._IsUrl(attachment)
        ext = this._GetExt(attachment)

        def RunSync(fn, *a, **k):
            return fn(*a, **k)

        async def RunAsync(fn, *a, **k):
            return await asyncio.to_thread(fn, *a, **k)

        def Run(fn, *a, **k):
            return RunSync(fn, *a, **k) if not isAsync else RunAsync(fn, *a, **k)

        async def DownloadIfNeeded(pathOrUrl, url, extFallback):
            if not isUrl:
                return str(pathOrUrl)
            p = this._TempPath(ext or extFallback)
            if not isAsync:
                this._DownloadTo(url, p)
                return p
            await asyncio.to_thread(this._DownloadTo, url, p)
            return p

        async def Upload(p):
            if isAsync:
                return await this.uploadAttachmentAsync(p, threadId, type)
            return this._RunCoro(this.uploadAttachmentAsync(p, threadId, type))

        async def Main():
            if ext in ("jpg", "jpeg", "png", "webp"):
                if isUrl:
                    w, h = await Run(this._GetImageWhRemote, attachment)
                    return await Run(this.sendImage, attachment, threadId, type, width=w, height=h, message=message, ttl=ttl)
                p = str(attachment)
                w, h = await Run(this._GetImageWhLocal, p)
                return await Run(this.sendLocalImage, p, threadId, type, width=w, height=h, message=message, ttl=ttl)

            if ext == "gif":
                p = await DownloadIfNeeded(attachment, attachment, "gif")
                w, h = await Run(this._GetImageWhLocal, p)
                thumb = kwargs.get("thumbnail") or kwargs.get("thumbnailUrl") or kwargs.get("thumb") or ""
                name = kwargs.get("gifName") or this._GetFileName(p, "gifBot.gif")
                return await Run(this.sendLocalGif, p, thumb, threadId, type, gifName=name, width=w, height=h, ttl=ttl)

            if ext in ("mp4", "mov", "mkv", "webm"):
                p = await DownloadIfNeeded(attachment, attachment, ext or "mp4")
                w, h, dur = await Run(this._ProbeVideo, p)
                uploaded = await Upload(p)
                if uploaded and uploaded.get("fileUrl"):
                    url = uploaded["fileUrl"]
                    thumb = kwargs.get("thumbnail") or kwargs.get("thumbnailUrl") or kwargs.get("thumb") or ""
                    return await Run(
                        this.sendVideo,
                        url,
                        thumb,
                        kwargs.get("duration", dur),
                        threadId,
                        type,
                        width=kwargs.get("width", w),
                        height=kwargs.get("height", h),
                        message=message,
                        ttl=ttl
                    )
                raise ZaloAPIException("Upload video failed")

            if ext in ("mp3", "aac", "m4a", "wav", "ogg", "opus"):
                p = await DownloadIfNeeded(attachment, attachment, ext or "mp3")
                uploaded = await Upload(p)
                if uploaded and uploaded.get("fileUrl"):
                    url = uploaded["fileUrl"]
                    size = await Run(this._GetLocalSize, p)
                    return await Run(this.sendVoice, url, threadId, type, fileSize=size, ttl=ttl)
                raise ZaloAPIException("Upload voice failed")

            p = await DownloadIfNeeded(attachment, attachment, ext or "bin")
            uploaded = await Upload(p)
            if uploaded and uploaded.get("fileUrl"):
                url = uploaded["fileUrl"]
                name = kwargs.get("fileName") or this._GetFileName(p, "default")
                size = kwargs.get("fileSize")
                if size is None:
                    size = await Run(this._GetLocalSize, p)
                ex = kwargs.get("extension") or this._GetExt(name) or (ext or "nullType")
                return await Run(this.sendFile, url, threadId, type, fileName=name, fileSize=size, extension=ex, ttl=ttl, local_path=p)

            raise ZaloAPIException("Upload file failed")

        if not isAsync:
            return this._RunCoro(Main())
        return Main()

    def _SendAttachmentCore(this, message, attachment, threadId, type, ttl=0, **kwargs):
        return this._SendAttachmentCoreImpl(message, attachment, threadId, type, ttl=ttl, isAsync=False, **kwargs)

    async def _SendAttachmentCoreAsync(this, message, attachment, threadId, type, ttl=0, **kwargs):
        return await this._SendAttachmentCoreImpl(message, attachment, threadId, type, ttl=ttl, isAsync=True, **kwargs)

    def _NormalizeSendArgs(this, args, kwargs):
        message = kwargs.pop("message", None)
        replyMsg = kwargs.pop("replyMsg", None)
        threadId = kwargs.pop("threadId", None)
        type = kwargs.pop("type", ThreadType.USER)
        mark_message = kwargs.pop("mark_message", None)
        ttl = kwargs.pop("ttl", 0)
        text = kwargs.pop("text", None)
        attachment = kwargs.pop("attachment", None)
        attachments = kwargs.pop("attachments", None)

        if attachment is None and attachments is not None:
            attachment = attachments

        n = len(args)
        if n == 0:
            return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs

        if n == 1:
            if message is None and isinstance(args[0], Message):
                message = args[0]
            else:
                message = message or args[0]
            return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs

        if n == 2:
            if isinstance(args[0], Message):
                if message is None:
                    message = args[0]
                if threadId is None:
                    threadId = args[1]
                return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs
            if message is None:
                message = args[0]
            if replyMsg is None:
                replyMsg = args[1]
            return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs

        if n == 3:
            if isinstance(args[0], Message):
                if message is None:
                    message = args[0]
                if threadId is None:
                    threadId = args[1]
                if type is None:
                    type = args[2]
                return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs
            if message is None:
                message = args[0]
            if replyMsg is None:
                replyMsg = args[1]
            if threadId is None:
                threadId = args[2]
            return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs

        if n >= 4:
            if isinstance(args[0], Message):
                if message is None:
                    message = args[0]
                if replyMsg is None:
                    replyMsg = args[1]
                if threadId is None:
                    threadId = args[2]
                if type is None:
                    type = args[3]
                return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs

            if message is None:
                message = args[0]
            if replyMsg is None:
                replyMsg = args[1]
            if threadId is None:
                threadId = args[2]
            if type is None:
                type = args[3]
            return message, replyMsg, threadId, type, mark_message, ttl, text, attachment, kwargs

    def send(this, *args, **kwargs):
        message, replyMsg, threadId, type, mark_message, ttl, text, attachment, rest = this._NormalizeSendArgs(args, kwargs)
        threadId = this._NormThreadId(threadId)

        if message is None and text is not None:
            message = Message(text=str(text))

        if message is not None and replyMsg is not None:
            return this.replyMessage(message, replyMsg, threadId, type, ttl)

        if attachment:
            if message is None:
                message = Message(text=str(text or ""))
            return this._SendAttachmentCore(message, attachment, threadId, type, ttl=ttl, **rest)

        if message is None:
            message = Message(text=str(text or ""))

        if this._IsUrl(message.text or ""):
            linkUrl = str(message.text).strip()
            msgText = rest.get("messageText")
            msg = Message(text=str(msgText or "")) if msgText is not None else Message(text="")
            return this._SendLinkAuto(linkUrl, threadId, type, msg, ttl)

        return this._SendTextCore(message, threadId, type, mark_message, ttl)

    async def sendAsync(this, *args, **kwargs):
        message, replyMsg, threadId, type, mark_message, ttl, text, attachment, rest = this._NormalizeSendArgs(args, kwargs)
        threadId = this._NormThreadId(threadId)

        if message is None and text is not None:
            message = Message(text=str(text))

        if message is not None and replyMsg is not None:
            return await this.replyMessageAsync(message, replyMsg, threadId, type, ttl)

        if attachment:
            if message is None:
                message = Message(text=str(text or ""))
            return await this._SendAttachmentCoreAsync(message, attachment, threadId, type, ttl=ttl, **rest)

        if message is None:
            message = Message(text=str(text or ""))

        if this._IsUrl(message.text or ""):
            linkUrl = str(message.text).strip()
            msgText = rest.get("messageText")
            msg = Message(text=str(msgText or "")) if msgText is not None else Message(text="")
            return await this._SendLinkAutoAsync(linkUrl, threadId, type, msg, ttl)

        return await this._SendTextCoreAsync(message, threadId, type, mark_message, ttl)

    async def sendImageAsync(this, image_url, threadId, type, width=2560, height=2560, message=None, ttl=0):
        if hasattr(super(), "sendImageAsync"):
            return await super().sendImageAsync(image_url, threadId, type, width=width, height=height, message=message, ttl=ttl)
        return await asyncio.to_thread(this.sendImage, image_url, threadId, type, width=width, height=height, message=message, ttl=ttl)

    async def sendLocalImageAsync(this, imagePath, threadId, type, width=2560, height=2560, message=None, custom_payload=None, ttl=0):
        if hasattr(super(), "sendLocalImageAsync"):
            return await super().sendLocalImageAsync(imagePath, threadId, type, width=width, height=height, message=message, custom_payload=custom_payload, ttl=ttl)
        return await asyncio.to_thread(this.sendLocalImage, imagePath, threadId, type, width=width, height=height, message=message, custom_payload=custom_payload, ttl=ttl)

    async def sendLocalGifAsync(this, gifPath, thumbnailUrl, threadId, type, gifName="gifBot.gif", width=500, height=500, ttl=0):
        if hasattr(super(), "sendLocalGifAsync"):
            return await super().sendLocalGifAsync(gifPath, thumbnailUrl, threadId, type, gifName=gifName, width=width, height=height, ttl=ttl)
        return await asyncio.to_thread(this.sendLocalGif, gifPath, thumbnailUrl, threadId, type, gifName=gifName, width=width, height=height, ttl=ttl)

    async def sendVideoAsync(this, videoUrl, thumbnailUrl, duration, threadId, type, width=1280, height=720, message=None, ttl=0):
        if hasattr(super(), "sendVideoAsync"):
            return await super().sendVideoAsync(videoUrl, thumbnailUrl, duration, threadId, type, width=width, height=height, message=message, ttl=ttl)
        return await asyncio.to_thread(this.sendVideo, videoUrl, thumbnailUrl, duration, threadId, type, width=width, height=height, message=message, ttl=ttl)

    async def sendVoiceAsync(this, voiceUrl, threadId, type, fileSize=None, ttl=0):
        if hasattr(super(), "sendVoiceAsync"):
            return await super().sendVoiceAsync(voiceUrl, threadId, type, fileSize=fileSize, ttl=ttl)
        return await asyncio.to_thread(this.sendVoice, voiceUrl, threadId, type, fileSize=fileSize, ttl=ttl)

    async def sendFileAsync(this, fileUrl, threadId, type, fileName="default", fileSize=None, extension="nullType", ttl=0, local_path=None):
        if hasattr(super(), "sendFileAsync"):
            return await super().sendFileAsync(fileUrl, threadId, type, fileName=fileName, fileSize=fileSize, extension=extension, ttl=ttl, local_path=local_path)
        return await asyncio.to_thread(this.sendFile, fileUrl, threadId, type, fileName=fileName, fileSize=fileSize, extension=extension, ttl=ttl, local_path=local_path)