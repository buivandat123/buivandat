from ....index import *

class SendImageApi:
    def _buildSendImage(this, imageUrl, threadId, type, width, height, message, ttl):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }
        clientId = utils.now()

        payloadParams = {
            "photoId": int(clientId * 2),
            "clientId": int(clientId),
            "desc": message.text if message else "",
            "width": int(width),
            "height": int(height),
            "rawUrl": imageUrl,
            "thumbUrl": imageUrl,
            "hdUrl": imageUrl,
            "thumbSize": "0",
            "fileSize": "0",
            "hdSize": "0",
            "zsource": -1,
            "jcp": json.dumps({ "sendSource": 1, "convertible": "jxl" }),
            "ttl": ttl,
            "imei": this._imei
        }

        if message and getattr(message, "mention", None):
            payloadParams["mentionInfo"] = message.mention

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/photo_original/send"
            payloadParams["toid"] = str(threadId)
            payloadParams["normalUrl"] = imageUrl
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/photo_original/send"
            payloadParams["grid"] = str(threadId)
            payloadParams["oriUrl"] = imageUrl
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, clientId, type

    def _parseSendImage(this, data, clientId, type):
        if data.get("error_code") == 0:
            results = data.get("data")
            if not results:
                raise ZaloAPIException("Error #1337 when sending image: Data is None")

            results = this._decode(results)
            results = results.get("data") or results

            if isinstance(results, dict):
                results["clientId"] = clientId
            elif isinstance(results, str):
                try:
                    results = json.loads(results)
                    results["clientId"] = clientId
                except Exception:
                    raise ZaloAPIException(f"Error #1337 when sending image: {results}")

            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending image: {data.get('error_message') or data.get('data')}"
        )

    def sendImage(this, imageUrl, threadId, type, width=2560, height=2560, message=None, ttl=0):
        url, params, payload, clientId, tType = this._buildSendImage(
            imageUrl, threadId, type, width, height, message, ttl
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendImage(data, clientId, tType)

    async def sendImageAsync(this, imageUrl, threadId, type, width=2560, height=2560, message=None, ttl=0):
        url, params, payload, clientId, tType = this._buildSendImage(
            imageUrl, threadId, type, width, height, message, ttl
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendImage(data, clientId, tType)