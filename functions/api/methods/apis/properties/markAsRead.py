from ....index import *

class MarkAsReadApi:
    """
    Message API: Mark message as read.

    Usage:
        api.markAsRead(...)
        await api.markAsReadAsync(...)
    """

    def _buildRead(this, msgId, cliMsgId, senderId, threadId, type, method):
        dest = "0" if type == ThreadType.USER else threadId
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0}

        info = {
            "data": [{
                "cmi": str(cliMsgId),
                "gmi": str(msgId),
                "si": str(senderId),
                "di": str(dest),
                "mt": method,
                "st": 3,
                "ts": str(utils.now())
            }]
        }

        p = {"msgInfos": info, "imei": this._imei}

        if type == ThreadType.USER:
            url = "https://tt-chat1-wpa.chat.zalo.me/api/message/seenv2"
            info["data"][0].update({"at": 7, "cmd": 501})
            p["senderId"] = str(dest)
        elif type == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/seenv2"
            info["data"][0].update({"at": 0, "cmd": 511})
            p["grid"] = str(dest)
        else:
            raise ZaloUserError("Thread type is invalid")

        p["msgInfos"] = json.dumps(info)
        return url, params, {"params": this._encode(p)}

    def _parseRead(this, data, msgId, threadId, type):
        if data.get("error_code") == 0:
            this.onMarkedSeen(msgId, threadId, type, utils.now())
            return True
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def markAsRead(this, msgId, cliMsgId, senderId, threadId, type, method="webchat"):
        """
        Mark message as read (sync).
        """
        url, params, payload = this._buildRead(
            msgId, cliMsgId, senderId, threadId, type, method
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseRead(data, msgId, threadId, type)

    async def markAsReadAsync(this, msgId, cliMsgId, senderId, threadId, type, method="webchat"):
        """
        Mark message as read (async).
        """
        url, params, payload = this._buildRead(
            msgId, cliMsgId, senderId, threadId, type, method
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseRead(data, msgId, threadId, type)
