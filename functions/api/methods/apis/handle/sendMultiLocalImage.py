from ....index import *

class SendMultiLocalImageApi:
    """
    Message API: Send multiple local images.

    Usage:
        api.sendMultiLocalImage(
            imagePathList,
            threadId,
            type,
            width=2560,
            height=2560,
            message=None,
        )

        await api.sendMultiLocalImageAsync(
            imagePathList,
            threadId,
            type,
            width=2560,
            height=2560,
            message=None,
        )
    """

    def _buildSendMultiLocalImageItems(this, imagePathList, threadId, type, width, height, message, ttl):
        if not isinstance(imagePathList, list) or len(imagePathList) < 1:
            raise ZaloUserError("image path must be a list to be able to send multiple at once.")

        groupLayoutId = str(utils.now())
        total = len(imagePathList)
        items = []

        for i, imagePath in enumerate(imagePathList):
            uploadImage = this.uploadImage(imagePath, threadId, type)

            payloadParams = {
                "photoId": uploadImage.get("photoId", int(utils.now() * 2)),
                "clientId": uploadImage.get("clientFileId", int(utils.now() - 1000)),
                "desc": (message.text if message else "") or "",
                "width": int(width),
                "height": int(height),
                "groupLayoutId": groupLayoutId,
                "totalItemInGroup": total,
                "isGroupLayout": 1,
                "idInGroup": int(i),
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
                payloadParams["toid"] = str(threadId)
                payloadParams["normalUrl"] = uploadImage["normalUrl"]
            elif type == ThreadType.GROUP:
                payloadParams["grid"] = str(threadId)
                payloadParams["oriUrl"] = uploadImage["normalUrl"]
            else:
                raise ZaloUserError("Thread type is invalid")

            items.append((imagePath, { "params": payloadParams }))

        return items

    def sendMultiLocalImage(this, imagePathList, threadId, type, width=2560, height=2560, message=None, ttl=0):
        items = this._buildSendMultiLocalImageItems(imagePathList, threadId, type, width, height, message, ttl)
        uploadData = []

        for imagePath, customPayload in items:
            r = this.sendLocalImage(
                imagePath,
                threadId,
                type,
                width,
                height,
                message,
                custom_payload=customPayload,
                ttl=ttl
            )
            uploadData.append(r.toDict() if hasattr(r, "toDict") else r)

        return Group.fromDict(uploadData, None) if type == ThreadType.GROUP else User.fromDict(uploadData, None)

    async def sendMultiLocalImageAsync(this, imagePathList, threadId, type, width=2560, height=2560, message=None, ttl=0):
        items = this._buildSendMultiLocalImageItems(imagePathList, threadId, type, width, height, message, ttl)
        uploadData = []

        for imagePath, customPayload in items:
            r = await this.sendLocalImageAsync(
                imagePath,
                threadId,
                type,
                width,
                height,
                message,
                custom_payload=customPayload,
                ttl=ttl
            )
            uploadData.append(r.toDict() if hasattr(r, "toDict") else r)

        return Group.fromDict(uploadData, None) if type == ThreadType.GROUP else User.fromDict(uploadData, None)