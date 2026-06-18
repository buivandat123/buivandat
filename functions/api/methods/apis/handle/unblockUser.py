from ....index import *

class UnblockUserApi:
    """
    Friend API: Unblock user by ID.

    Usage:
        r = api.unblockUser(userId)
        r = await api.unblockUserAsync(userId)
    """

    def _buildUnblockUser(this, userId):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "fid": str(userId),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-friend-wpa.chat.zalo.me/api/friend/unblock"
        return url, params, payload

    def _parseUnblockUser(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        results = this._decode(results)
        results = results.get("data") if isinstance(results, dict) and results.get("data") else results

        if results is None:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                raise ZaloAPIException(f"Error #1337 when sending requests: {results}")

        return User.fromDict(results, None)

    def unblockUser(this, userId):
        url, params, payload = this._buildUnblockUser(userId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseUnblockUser(data)

    async def unblockUserAsync(this, userId):
        url, params, payload = this._buildUnblockUser(userId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseUnblockUser(data)