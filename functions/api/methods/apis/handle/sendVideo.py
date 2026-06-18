from ....index import *

class SendVideoApi:
    """
    Message API: Send (forward) video by url.

    Usage:
        api.sendVideo(videoUrl, thumbnailUrl, duration, threadId, type, message=msg)
        await api.sendVideoAsync(videoUrl, thumbnailUrl, duration, threadId, type, message=msg)
    """

    def _buildSendVideo(this, videoUrl, thumbnailUrl, duration, threadId, type, width, height, message, ttl):
        try:
            r = this._state._session.head(videoUrl)
            if r.status_code == 200:
                fileSize = int(r.headers.get("Content-Length") or 0)
            else:
                fileSize = 0
        except Exception as e:
            raise ZaloAPIException(f"Unable to get url content: {e}")

        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }

        msgInfo = {
            "videoUrl": str(videoUrl),
            "thumbUrl": str(thumbnailUrl),
            "duration": int(duration),
            "width": int(width),
            "height": int(height),
            "fileSize": int(fileSize),
            "properties": {
                "color": -1,
                "size": -1,
                "type": 1003,
                "subType": 0,
                "ext": {
                    "sSrcType": -1,
                    "sSrcStr": "",
                    "msg_warning_type": 0
                }
            },
            "title": (message.text or "") if message else ""
        }

        payloadParams = {
            "clientId": str(utils.now()),
            "ttl": ttl,
            "zsource": 704,
            "msgType": 5,
            "msgInfo": json.dumps(msgInfo)
        }

        if message and getattr(message, "mention", None):
            payloadParams["mentionInfo"] = message.mention

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/forward"
            payloadParams["toId"] = str(threadId)
            payloadParams["imei"] = this._imei
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/forward"
            payloadParams["visibility"] = 0
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, type

    def _parseSendVideo(this, data, type):
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

    def sendVideo(this, videoUrl, thumbnailUrl, duration, threadId, type, width=1280, height=720, message=None, ttl=0):
        url, params, payload, tType = this._buildSendVideo(
            videoUrl, thumbnailUrl, duration, threadId, type, width, height, message, ttl
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendVideo(data, tType)

    async def sendVideoAsync(this, videoUrl, thumbnailUrl, duration, threadId, type, width=1280, height=720, message=None, ttl=0):
        url, params, payload, tType = this._buildSendVideo(
            videoUrl, thumbnailUrl, duration, threadId, type, width, height, message, ttl
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendVideo(data, tType)