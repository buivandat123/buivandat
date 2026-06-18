from .....index import *

class UpdateAutoDeleteChatApi:
    def _buildUpdateAutoDeleteChat(this, ttl, threadId, type):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "threadId": str(threadId),
                "isGroup": 1 if type == ThreadType.GROUP else 0,
                "ttl": int(ttl),
                "clientLang": getattr(this, "language", "vi")
            })
        }

        url = "https://tt-convers-wpa.chat.zalo.me/api/conv/autodelete/updateConvers"
        return url, params, payload

    def _parseUpdateAutoDeleteChat(this, data):
        if data.get("error_code") != 0:
            raise ZaloAPIException(
                f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
            )
        result = data.get("data") or ""
        final = this._decode(result)
        return final

    def updateAutoDeleteChat(this, ttl, threadId, type):
        url, params, payload = this._buildUpdateAutoDeleteChat(ttl, threadId, type)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseUpdateAutoDeleteChat(data)

    async def updateAutoDeleteChatAsync(this, ttl, threadId, type):
        url, params, payload = this._buildUpdateAutoDeleteChat(ttl, threadId, type)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseUpdateAutoDeleteChat(data)