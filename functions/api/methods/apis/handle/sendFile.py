from ....index import *

class SendFileApi:
    """
    Message API: Send file by url.

    Usage:
        api.sendFile(fileUrl, threadId, type, fileName="a.txt")
        await api.sendFileAsync(fileUrl, threadId, type, fileName="a.txt")
    """

    def _buildSendFile(this, fileUrl, threadId, type, fileName, fileSize, extension, ttl, local_path):
        fileChecksum = None
        contentBytes = None

        if local_path and os.path.exists(local_path):
            with open(local_path, "rb") as f:
                contentBytes = f.read()
            fileChecksum = hashlib.md5(contentBytes).hexdigest()
            if not fileSize:
                fileSize = len(contentBytes)
        elif not fileSize:
            try:
                r = this._state._session.get(fileUrl)
                if r.status_code == 200:
                    contentBytes = r.content
                    fileSize = int(r.headers.get("Content-Length") or len(contentBytes))
                    fileChecksum = hashlib.md5(contentBytes).hexdigest()
                else:
                    fileSize = 0
                    fileChecksum = hashlib.md5(b"").hexdigest()
            except:
                raise ZaloAPIException("Unable to get url content")
        else:
            fileChecksum = hashlib.md5(b"").hexdigest()

        parts = str(fileName or "").rsplit(".", 1)
        if len(parts) == 2 and parts[1]:
            extension = parts[1]

        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }

        payloadParams = {
            "fileId": str(int(utils.now() * 2)),
            "checksum": fileChecksum,
            "checksumSha": "",
            "extension": extension,
            "totalSize": int(fileSize or 0),
            "fileName": fileName,
            "clientId": utils.now(),
            "fType": 1,
            "fileCount": 0,
            "fdata": "{}",
            "fileUrl": fileUrl,
            "zsource": 401,
            "ttl": ttl
        }

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/asyncfile/msg"
            payloadParams["toid"] = str(threadId)
            payloadParams["imei"] = this._imei
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/asyncfile/msg"
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, type

    def _parseSendFile(this, data, type):
        results = data.get("data") if data.get("error_code") == 0 else None
        if results:
            results = this._decode(results)
            results = results.get("data") if isinstance(results, dict) and results.get("data") else results
            if results is None:
                results = { "error_code": 1337, "error_message": "Data is None" }

            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    results = { "error_code": 1337, "error_message": results }

            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )

    def sendFile(this, fileUrl, threadId, type, fileName="default", fileSize=None, extension="nullType", ttl=0, local_path=None):
        url, params, payload, tType = this._buildSendFile(
            fileUrl, threadId, type, fileName, fileSize, extension, ttl, local_path
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendFile(data, tType)

    async def sendFileAsync(this, fileUrl, threadId, type, fileName="default", fileSize=None, extension="nullType", ttl=0, local_path=None):
        url, params, payload, tType = this._buildSendFile(
            fileUrl, threadId, type, fileName, fileSize, extension, ttl, local_path
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendFile(data, tType)