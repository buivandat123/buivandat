from ....index import *

class SetTypingApi:
    """
    Message API: Send typing indicator.

    Usage:
        api.setTyping(threadId, ThreadType.USER)
        await api.setTypingAsync(threadId, ThreadType.USER)
    """

    def _buildSetTyping(this, threadId, type):
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}
        p = {"imei": this._imei}

        if type == ThreadType.USER:
            url = "https://tt-chat1-wpa.chat.zalo.me/api/message/typing"
            p.update({"toid": str(threadId), "destType": 3})
        elif type == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/typing"
            p["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        return url, params, {"params": this._encode(p)}

    def _parseSetTyping(this, data):
        if data.get("error_code") == 0:
            return True
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def setTyping(this, threadId, type):
        """
        Send typing indicator (sync).
        """
        url, params, payload = this._buildSetTyping(threadId, type)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSetTyping(data)

    async def setTypingAsync(this, threadId, type):
        """
        Send typing indicator (async).
        """
        url, params, payload = this._buildSetTyping(threadId, type)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSetTyping(data)
