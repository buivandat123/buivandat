from ....index import *

class MarkAsDeliveredApi:
    """
    Message API: Mark message as delivered.

    Usage:
        api.markAsDelivered(...)
        await api.markAsDeliveredAsync(...)
    """

    def _buildDelivered(this, msgId, cliMsgId, senderId, threadId, type, method):
        dest = "0" if type == ThreadType.USER else threadId
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}

        info = {
            "seen": 0,
            "data": [{
                "cmi": str(cliMsgId),
                "gmi": str(msgId),
                "si": str(senderId),
                "di": str(dest),
                "mt": method,
                "st": 3,
                "at": 0,
                "ts": str(utils.now())
            }]
        }

        p = {"msgInfos": info}

        if type == ThreadType.USER:
            url = "https://tt-chat3-wpa.chat.zalo.me/api/message/deliveredv2"
            info["data"][0]["cmd"] = 501
        else:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/deliveredv2"
            info["data"][0]["cmd"] = 521
            info["grid"] = str(dest)
            p["imei"] = this._imei

        p["msgInfos"] = json.dumps(info)
        return url, params, {"params": this._encode(p)}

    def _parseDelivered(this, data, msgId, threadId, type):
        if data.get("error_code") == 0:
            this.messageListenerDelivered(msgId, threadId, type, utils.now())
            return True
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def markAsDelivered(this, msgId, cliMsgId, senderId, threadId, type, method="webchat"):
        """
        Mark message as delivered (sync).
        """
        url, params, payload = this._buildDelivered(
            msgId, cliMsgId, senderId, threadId, type, method
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseDelivered(data, msgId, threadId, type)

    async def markAsDeliveredAsync(this, msgId, cliMsgId, senderId, threadId, type, method="webchat"):
        """
        Mark message as delivered (async).
        """
        url, params, payload = this._buildDelivered(
            msgId, cliMsgId, senderId, threadId, type, method
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseDelivered(data, msgId, threadId, type)
