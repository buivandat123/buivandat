from .....index import *

class uploadAttachmentApi:
    RetryCount = 5
    WsWaitTimeout = 2
    PostTimeout = 10
    AsyncTimeout = 15
    MaxConcurrentChunks = 10 * 4
    MaxBatchInflight = 2

    ZpwVer = 649
    Kb = 1000
    Mb = 1000
    MaxSizeMb = 9
    ChunkSize = 3145728                                                             

    def _Join(this, a):
        return "".join(a)

    def _Lower(this, s):
        return str(s or "").lower()

    def _GetExt(this, p):
        return os.path.splitext(str(p or ""))[1][1:].lower()

    def _PickFileType(this, ext, fileSize, maxSize, maxtypeName):
        maxtype = ""
        e = this._Lower(ext)
        if e in ["jpg", "jpeg", "png"]:
            return "image", maxtype
        if e in ["mp3", "aac", "m4a", "flac"]:
            if fileSize > maxSize:
                maxtype = maxtypeName
                return "others", maxtype
            return "aac", maxtype
        if e == "mp4":
            return "video", maxtype
        return "others", maxtype

    def _BuildUploadUrls(this):
        return {
            "image": "photo_original/upload",
            "aac": "voice/upload",
            "video": "asyncfile/upload",
            "gif": "gif?",
            "others": "asyncfile/upload",
        }

    def _BuildBase(this, threadId, type):
        base = "https://tt-files-wpa.chat.zalo.me/api/"
        if type == ThreadType.USER:
            return base + "message/", {"type": 2}, {"toid": str(threadId)}
        return base + "group/", {"type": 11}, {"grid": str(threadId)}

    def _BuildChunkParams(this, totalChunks, filePath, fileType, clientId, fileSize, chunkId, paramsExtra):
        return {
            "totalChunk": totalChunks,
            "fileName": os.path.basename(filePath),
            "fileType": fileType,
            "clientId": clientId,
            "totalSize": fileSize,
            "imei": this._imei,
            "isE2EE": 0,
            "jxl": 0,
            "chunkId": chunkId,
            **paramsExtra,
        }

    def _BuildAiohttpForm(this, filePath, chunk):
        f = aiohttp.FormData()
        f.add_field(
            "chunkContent",
            chunk,
            filename=os.path.basename(filePath),
            content_type="application/octet-stream",
        )
        return f

    def _FailPayload(this, filePath, fileType, reason, maxtype=""):
        return {
            "ok": False,
            "reason": str(reason or "upload_failed"),
            "fileName": os.path.basename(filePath),
            "totalSize": os.path.getsize(filePath) if os.path.exists(filePath) else 0,
            "fileType": fileType or "others",
            "fileUrl": "",
            "fileId": "-1",
            "maxtype": maxtype or "",
        }

    async def _WaitWsCallback(this, filePath, fileType, fileId, maxtype):
        e = asyncio.Event()
        r = {}

        async def CallbackAsync(ws_data):
            r.update(
                {
                    "fileName": os.path.basename(filePath),
                    "totalSize": os.path.getsize(filePath),
                    "fileType": fileType,
                    "fileUrl": ws_data.get("fileUrl", ""),
                    "fileId": ws_data.get("fileId", fileId),
                }
            )
            e.set()

        this.uploadAsyncCallbacks[str(fileId)] = CallbackAsync

        while True:
            try:
                await asyncio.wait_for(e.wait(), timeout=this.WsWaitTimeout)
                break
            except asyncio.TimeoutError:
                pass

        if maxtype and r.get("fileUrl"):
            r["fileUrl"] = f"{r['fileUrl']}/{maxtype}"
        r["ok"] = bool(r.get("fileUrl") or r.get("fileId"))
        return r

    async def _ReadChunksAsync(this, filePath, chunkSize):
        chunks = []
        async with aiofiles.open(filePath, "rb") as f:
            while True:
                b = await f.read(chunkSize)
                if not b:
                    break
                chunks.append(b)
        return chunks

    async def uploadAttachmentAsync(this, filePath, threadId, type):
        if not os.path.exists(filePath):
            raise ZaloUserError(f"{filePath} not found")

        ext = this._GetExt(filePath)
        urlType = this._BuildUploadUrls()

        maxSize = this.MaxSizeMb * this.Mb * this.Mb
        fileSize = os.path.getsize(filePath)
        fileType, maxtype = this._PickFileType(
            ext, fileSize, maxSize, f"{this.userName(this.uid).replace(' ', '-')}.aac"
        )

        baseUrl, baseParams, paramsExtra = this._BuildBase(threadId, type)
        baseParams = dict(baseParams)
        baseParams.update({"zpw_ver": this.ZpwVer, "zpw_type": this.apiLogintype})

        chunkSize = this.ChunkSize
        totalChunks = math.ceil(fileSize / chunkSize)
        clientId = int(time.time() * 1000)

        chunks = await this._ReadChunksAsync(filePath, chunkSize)
        if not chunks:
            return this._FailPayload(filePath, fileType, "empty_file", maxtype)

        async def UploadSingleChunk(chunkId, chunk):
            u = baseUrl + urlType[fileType]
            for _ in range(this.RetryCount):
                try:
                    chunkParams = this._BuildChunkParams(
                        totalChunks, filePath, fileType, clientId, fileSize, chunkId, paramsExtra
                    )
                    p = dict(baseParams)
                    p["params"] = this._encode(chunkParams)
                    form = this._BuildAiohttpForm(filePath, chunk)
                    data = await this.PostSessionAsync(u, params=p, data=form, timeout=this.AsyncTimeout)
                    if data and data.get("error_code") == 0:
                        dec = this._decode(data["data"])
                        if dec.get("error_code") == 0:
                            d = dec.get("data") or {}
                            if d.get("fileId") and d["fileId"] != "-1":
                                return await this._WaitWsCallback(filePath, fileType, d["fileId"], maxtype)
                            if d.get("photoId") and d.get("finished"):
                                d["ok"] = True
                                return {"fileType": fileType, **d}
                except Exception:
                    pass
            return None

        sem = asyncio.Semaphore(this.MaxConcurrentChunks)
        prog = {"u": 0}

        async def LimitedUpload(i, c):
            async with sem:
                r = await UploadSingleChunk(i + 1, c)
                prog["u"] += 1
                pct = (prog["u"] / totalChunks) * 100
                print(f"\rUpload progress: {prog['u']}/{totalChunks} chunks ({pct:.2f}%)", end="")
                return r

        results = await asyncio.gather(*[LimitedUpload(i, c) for i, c in enumerate(chunks)], return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and (r.get("fileUrl") or r.get("photoId") or r.get("fileId")):
                r["ok"] = True
                print(f"\n{r}")
                return r

        results2 = await asyncio.gather(*[UploadSingleChunk(i + 1, c) for i, c in enumerate(chunks)], return_exceptions=True)
        for r in results2:
            if isinstance(r, dict) and (r.get("fileUrl") or r.get("photoId") or r.get("fileId")):
                r["ok"] = True
                print(f"\n{r}")
                return r

        return this._FailPayload(filePath, fileType, "no_successful_chunk", maxtype)

    def uploadAttachment(this, filePath, threadId, type):
        if not os.path.exists(filePath):
            raise ZaloUserError(f"{filePath} not found")

        ext = this._GetExt(filePath)
        urlType = this._BuildUploadUrls()

        maxSize = this.MaxSizeMb * this.Mb * this.Mb
        fileSize = os.path.getsize(filePath)
        fileType, maxtype = this._PickFileType(ext, fileSize, maxSize, f"{this.userName(this.uid).replace(' ', '-')}.aac")

        baseUrl, baseParams, paramsExtra = this._BuildBase(threadId, type)
        baseParams = dict(baseParams)
        baseParams.update({"zpw_ver": this.ZpwVer, "zpw_type": this.apiLogintype})

        chunkSize = this.ChunkSize
        totalChunks = math.ceil(fileSize / chunkSize)
        clientId = int(time.time() * 1000)

        def UploadSingleChunk(chunkId, chunk):
            u = baseUrl + urlType[fileType]
            for _ in range(this.RetryCount):
                try:
                    chunkParams = this._BuildChunkParams(
                        totalChunks, filePath, fileType, clientId, fileSize, chunkId, paramsExtra
                    )
                    p = dict(baseParams)
                    p["params"] = this._encode(chunkParams)
                    files = [("chunkContent", (os.path.basename(filePath), chunk, "application/octet-stream"))]
                    resp = this.PostSession(u, params=p, files=files, timeout=this.PostTimeout)
                    data = resp.json()
                    if data and data.get("error_code") == 0:
                        dec = this._decode(data["data"])
                        if dec.get("error_code") == 0:
                            d = dec.get("data") or {}
                            if d.get("fileId") and d["fileId"] != "-1":
                                fut = Future()

                                def Callback(ws_data):
                                    fut.set_result(
                                        {
                                            "ok": True,
                                            "fileName": os.path.basename(filePath),
                                            "totalSize": os.path.getsize(filePath),
                                            "fileType": fileType,
                                            "fileUrl": ws_data.get("fileUrl", ""),
                                            "fileId": ws_data.get("fileId", d["fileId"]),
                                        }
                                    )

                                this.uploadCallbacks[str(d["fileId"])] = Callback
                                r = fut.result()
                                if maxtype and r.get("fileUrl"):
                                    r["fileUrl"] = f"{r['fileUrl']}/{maxtype}"
                                return True, r

                            if d.get("photoId") and d.get("finished"):
                                d["ok"] = True
                                return True, {"fileType": fileType, **d}
                except Exception:
                    pass
            return False, None

        uploadedChunks = 0
        with open(filePath, "rb") as f, ThreadPoolExecutor(max_workers=this.PostTimeout) as executor:
            chunkId = 1
            while chunkId <= totalChunks:
                futures = []
                for _ in range(this.MaxBatchInflight):
                    chunk = f.read(chunkSize)
                    if not chunk:
                        break
                    futures.append(executor.submit(UploadSingleChunk, chunkId, chunk))
                    chunkId += 1

                for fu in futures:
                    ok, r = fu.result()
                    if ok:
                        uploadedChunks += 1
                        pct = (uploadedChunks / totalChunks) * 100
                        print(f"\rUpload progress: {uploadedChunks}/{totalChunks} chunks ({pct:.2f}%)", end="")
                        if isinstance(r, dict) and (r.get("fileUrl") or r.get("photoId") or r.get("fileId")):
                            r["ok"] = True
                            print(f"\n{r}")
                            return r

        return this._FailPayload(filePath, fileType, "no_successful_chunk", maxtype)