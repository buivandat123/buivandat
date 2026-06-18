from ....index import *

class SendStickerApi:
    """
    Message API: Send sticker by Object

    Usage:
        api.sendSticker(stickerType, stickerId, cateId, threadId, type)
        await api.sendStickerAsync(stickerType, stickerId, cateId, threadId, type)
    """
    def _buildSendSticker(this, stickerType, stickerId, cateId, threadId, type, ttl):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }

        payloadParams = {
            "stickerId": int(stickerId),
            "cateId": int(cateId),
            "type": int(stickerType),
            "clientId": utils.now(),
            "imei": this._imei,
            "ttl": ttl
        }

        if type == ThreadType.USER:
            url = "https://tt-chat2-wpa.chat.zalo.me/api/message/sticker"
            payloadParams["zsource"] = 106
            payloadParams["toid"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/sticker"
            payloadParams["zsource"] = 103
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, type

    def _parseSendSticker(this, data, type):
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

    def sendSticker(this, stickerType, stickerId, cateId, threadId, type, ttl=0):
        url, params, payload, tType = this._buildSendSticker(
            stickerType, stickerId, cateId, threadId, type, ttl
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendSticker(data, tType)

    async def sendStickerAsync(this, stickerType, stickerId, cateId, threadId, type, ttl=0):
        url, params, payload, tType = this._buildSendSticker(
            stickerType, stickerId, cateId, threadId, type, ttl
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendSticker(data, tType)