from ....index import *

class SendCustomStickerApi:
    def _buildSendCustomSticker(this, staticImgUrl, animationImgUrl, threadId, type, reply, width, height, ttl, ai):
        width = int(width) if width else 0
        height = int(height) if height else 0

        params = { "zpw_ver": 669, "zpw_type": this.apiLogintype, "nretry": 0 }

        payloadParams = {
            "clientId": utils.now(),
            "title": "",
            "oriUrl": staticImgUrl,
            "thumbUrl": staticImgUrl,
            "hdUrl": staticImgUrl,
            "width": width,
            "height": height,
            "properties": json.dumps({
                "subType": 0,
                "color": -1,
                "size": -1,
                "type": 3,
                "ext": json.dumps({
                    "sSrcStr": "",
                    "sSrcType": -1
                })
            }),
            "contentId": utils.now(),
            "thumb_height": width,
            "thumb_width": height,
            "webp": json.dumps({
                "width": width,
                "height": height,
                "url": animationImgUrl
            }),
            "zsource": -1,
            "ttl": ttl
        }

        if ai:
            payloadParams["jcp"] = json.dumps({ "pStickerType": 1 })

        if reply:
            payloadParams["refMessage"] = str(reply)

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/photo_url"
            payloadParams["toId"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/photo_url"
            payloadParams["visibility"] = 0
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, type

    def _parseSendCustomSticker(this, data, type):
        results = data.get("data") if data.get("error_code") == 0 else None
        if results:
            results = this._decode(results)
            results = results.get("data") if isinstance(results, dict) and results.get("data") else results

            if results is None:
                results = { "error_code": 1337, "error_message": "Data is None" }

            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except Exception:
                    results = { "error_code": 1337, "error_message": results }

            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )

    def sendCustomSticker(this, staticImgUrl, animationImgUrl, threadId, type, reply=None, width=None, height=None, ttl=0, ai=False):
        url, params, payload, tType = this._buildSendCustomSticker(
            staticImgUrl, animationImgUrl, threadId, type, reply, width, height, ttl, ai
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendCustomSticker(data, tType)

    async def sendCustomStickerAsync(this, staticImgUrl, animationImgUrl, threadId, type, reply=None, width=None, height=None, ttl=0, ai=False):
        url, params, payload, tType = this._buildSendCustomSticker(
            staticImgUrl, animationImgUrl, threadId, type, reply, width, height, ttl, ai
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendCustomSticker(data, tType)