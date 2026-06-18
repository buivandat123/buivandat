from ....index import *

class SendGifApi:
    """
    Message API: Send local gif.

    Usage:
        api.sendLocalGif(gifPath, thumbnailUrl, threadId, type)
        await api.sendLocalGifAsync(gifPath, thumbnailUrl, threadId, type)
    """

    def _buildSendLocalGif(this, gifPath, thumbnailUrl, threadId, type, gifName, width, height, ttl):
        if not os.path.exists(gifPath):
            raise ZaloUserError(f"{gifPath} not found")

        if not gifName:
            gifName = os.path.basename(gifPath) or "gifBot.gif"

        with open(gifPath, "rb") as f:
            buf = f.read()

        gifSize = len(buf)
        fileChecksum = hashlib.md5(buf).hexdigest()

        files = [("chunkContent", open(gifPath, "rb"))]

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "type": 1,
            "params": {
                "clientId": str(utils.now()),
                "fileName": gifName,
                "totalSize": gifSize,
                "width": int(width),
                "height": int(height),
                "msg": "",
                "type": 1,
                "ttl": ttl,
                "thumb": thumbnailUrl,
                "checksum": fileChecksum,
                "totalChunk": 1,
                "chunkId": 1
            }
        }

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/gif"
            params["params"]["toid"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/gif"
            params["params"]["visibility"] = 0
            params["params"]["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        params["params"] = this._encode(params["params"])
        return url, params, files, type

    def _parseSendLocalGif(this, data, type):
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

    def sendLocalGif(this, gifPath, thumbnailUrl, threadId, type, gifName="gifBot.gif", width=500, height=500, ttl=0):
        url, params, files, tType = this._buildSendLocalGif(
            gifPath, thumbnailUrl, threadId, type, gifName, width, height, ttl
        )
        data = this.PostSession(url, params=params, files=files).json()
        return this._parseSendLocalGif(data, tType)

    async def sendLocalGifAsync(this, gifPath, thumbnailUrl, threadId, type, gifName="gifBot.gif", width=500, height=500, ttl=0):
        url, params, files, tType = this._buildSendLocalGif(
            gifPath, thumbnailUrl, threadId, type, gifName, width, height, ttl
        )
        data = await this.PostSessionAsync(url, params=params, files=files)
        return this._parseSendLocalGif(data, tType)