from ....index import *

class ListFriendRequestsApi:
    """
    Friend API: List pending friend requests (incoming).

    Usage:
        r = api.listFriendRequests()
        r = await api.listFriendRequestsAsync()
    """

    def _buildListFriendRequests(this):
        params = {
            "zpw_ver": 664,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-friend-wpa.chat.zalo.me/api/friend/recommendsv2/list"
        return url, params, payload

    def _parseListFriendRequests(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} - {errorMessage}")

        results = data.get("data")
        if not results:
            return []

        if isinstance(results, str):
            try:
                results = this._decode(results)
            except:
                raise ZaloAPIException("Error #1337 - Decode failed")

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                raise ZaloAPIException("Error #1337 - Invalid JSON data")

        return results

    def listFriendRequests(this):
        url, params, payload = this._buildListFriendRequests()
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseListFriendRequests(data)

    async def listFriendRequestsAsync(this):
        url, params, payload = this._buildListFriendRequests()
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseListFriendRequests(data)