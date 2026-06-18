from ....index import *

class SetAliasApi:
    """
    Friend API: Set alias (nickname) for a friend by ID.

    Usage:
        r = api.setAlias(friendId, "Yêuuuuuuuu")
        r = await api.setAliasAsync(friendId, "Yêuuuuuuuu")
    """

    def _buildSetAlias(this, friendId, alias):
        params = {
            "zpw_ver": 677,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "friendId": str(friendId),
                "alias": str(alias),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-alias-wpa.chat.zalo.me/api/alias/update"
        return url, params

    def _parseSetAlias(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            return None

        results = this._decode(results) if isinstance(results, str) else results
        if isinstance(results, dict) and results.get("data") is not None:
            return results.get("data")

        return results

    def setAlias(this, friendId, alias):
        url, params = this._buildSetAlias(friendId, alias)
        data = this.GetSession(url, params=params).json()
        return this._parseSetAlias(data)

    async def setAliasAsync(this, friendId, alias):
        url, params = this._buildSetAlias(friendId, alias)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseSetAlias(data)