from ....index import *

class GetGroupLinkApi:
    """
    Group API: Get group invite link detail.

    Usage:
        r = api.getGroupLink(groupId)
        r = await api.getGroupLinkAsync(groupId)

    Returns:
        dict:
            decoded data dict if success
            or { "error": str } if failed
    """

    def _buildGetGroupLink(this, threadId):
        if not threadId:
            raise ValueError("threadId is required")

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grid": str(threadId),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/link/detail"
        return url, params

    def _parseGetGroupLink(this, data):
        if data.get("error_code") != 0:
            return { "error": str(data.get("error_message") or data.get("data") or data.get("error_code")) }

        raw = data.get("data")
        if not raw:
            return { "error": "Data is None" }

        decoded = this._decode(raw) if isinstance(raw, str) else raw

        if isinstance(decoded, str):
            try:
                decoded = json.loads(decoded)
            except:
                return { "error": "Invalid response format" }

        if isinstance(decoded, dict):
            return decoded

        return { "error": "Invalid response format" }

    def getGroupLink(this, threadId):
        url, params = this._buildGetGroupLink(threadId)
        try:
            data = this.GetSession(url, params=params).json()
            return this._parseGetGroupLink(data)
        except ZaloAPIException as e:
            return { "error": str(e) }
        except Exception as e:
            return { "error": f"An unexpected error occurred: {str(e)}" }

    async def getGroupLinkAsync(this, threadId):
        url, params = this._buildGetGroupLink(threadId)
        try:
            data = await this.GetSessionAsync(url, params=params)
            return this._parseGetGroupLink(data)
        except ZaloAPIException as e:
            return { "error": str(e) }
        except Exception as e:
            return { "error": f"An unexpected error occurred: {str(e)}" }