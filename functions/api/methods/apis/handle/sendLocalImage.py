from ....index import *

class SendLocalImageApi:
    def _buildSendLocalImage(this, imagePath, threadId, type, width, height, message, customPayload, ttl):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }

        if customPayload:
            if type == ThreadType.USER:
                url = "https://tt-files-wpa.chat.zalo.me/api/message/photo_original/send"
            elif type == ThreadType.GROUP:
                url = "https://tt-files-wpa.chat.zalo.me/api/group/photo_original/send"
            else:
                raise ZaloUserError("Thread type is invalid")
            payload = customPayload
            payloadParams = payload.get("params") if isinstance(payload, dict) else None
            if not isinstance(payloadParams, dict):
                raise ZaloUserError("custom_payload is invalid")
        else:
            uploadImage = this.uploadImage(imagePath, threadId, type)

            payloadParams = {
                "photoId": uploadImage.get("photoId", int(utils.now() * 2)),
                "clientId": uploadImage.get("clientFileId", int(utils.now() - 1000)),
                "desc": (message.text if message else "") or "",
                "width": int(width),
                "height": int(height),
                "rawUrl": uploadImage["normalUrl"],
                "thumbUrl": uploadImage["thumbUrl"],
                "hdUrl": uploadImage["hdUrl"],
                "thumbSize": "53932",
                "fileSize": "247671",
                "hdSize": "344622",
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
                payloadParams["normalUrl"] = uploadImage["normalUrl"]
            elif type == ThreadType.GROUP:
                url = "https://tt-files-wpa.chat.zalo.me/api/group/photo_original/send"
                payloadParams["grid"] = str(threadId)
                payloadParams["oriUrl"] = uploadImage["normalUrl"]
            else:
                raise ZaloUserError("Thread type is invalid")

            payload = { "params": payloadParams }

        payload["params"] = this._encode(payload["params"])
        return url, params, payload, type

    def _parseSendLocalImage(this, data, type):
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

    def sendLocalImage(this, imagePath, threadId, type, width=2560, height=2560, message=None, custom_payload=None, ttl=0):
        url, params, payload, tType = this._buildSendLocalImage(
            imagePath, threadId, type, width, height, message, custom_payload, ttl
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendLocalImage(data, tType)

    async def sendLocalImageAsync(this, imagePath, threadId, type, width=2560, height=2560, message=None, custom_payload=None, ttl=0):
        url, params, payload, tType = this._buildSendLocalImage(
            imagePath, threadId, type, width, height, message, custom_payload, ttl
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendLocalImage(data, tType)