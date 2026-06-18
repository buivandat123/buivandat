from ....index import *
import time

class SendMultiImageApi:
    def _buildSendMultiImageItem(this, imageUrlList, threadId, type, width, height, message, ttl):
        if not isinstance(imageUrlList, list) or not imageUrlList:
            raise ZaloUserError("image url must be a list to be able to send multiple at once.")

        groupLayoutId = str(time.time_ns())
        total = len(imageUrlList)
        baseSeed = time.time_ns()

        payloads = []

        for i, imageUrl in enumerate(imageUrlList):
            clientId = baseSeed + i + 1
            photoId = (clientId << 1) & 0x7FFFFFFFFFFFFFFF

            payloadParams = {
                "photoId": int(photoId),
                "clientId": str(clientId),
                "desc": (message.text if message else "") or "",
                "width": int(width),
                "height": int(height),
                "groupLayoutId": groupLayoutId,
                "totalItemInGroup": int(total),
                "isGroupLayout": 1,
                "idInGroup": int(i),
                "rawUrl": imageUrl,
                "thumbUrl": imageUrl,
                "hdUrl": imageUrl,
                "zsource": -1,
                "jcp": json.dumps({ "sendSource": 1, "convertible": "jxl" }),
                "ttl": int(ttl),
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

            payload = {
                "zpw_ver": 649,
                "zpw_type": this.apiLogintype,
                "nretry": 0,
                "params": this._encode(payloadParams)
            }

            payloads.append((url, payload, type, clientId))

        return payloads

    def _parseSendMultiImageItem(this, data, clientId, type):
        if data.get("error_code") != 0:
            raise ZaloAPIException(f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}")

        results = data.get("data")
        if not results:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        results = this._decode(results)
        results = results.get("data") if isinstance(results, dict) and results.get("data") else (results.get("data") or results)

        if results is None:
            results = { "error_code": 1337, "error_message": "Data is None" }

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                results = { "error_code": 1337, "error_message": results }

        if isinstance(results, dict):
            results["clientId"] = str(clientId)

        return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

    def sendMultiImage(this, imageUrlList, threadId, type, width=2560, height=2560, message=None, ttl=0):
        payloads = this._buildSendMultiImageItem(imageUrlList, threadId, type, width, height, message, ttl)
        out = []
        for url, payload, tType, clientId in payloads:
            data = this.PostSession(url, data=payload).json()
            out.append(this._parseSendMultiImageItem(data, clientId, tType))
        return out