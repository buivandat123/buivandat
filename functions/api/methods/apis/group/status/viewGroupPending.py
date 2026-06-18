from .....index import *

class ViewGroupPendingApi:
    """
    Group API: View list of pending approval members in group by ID.

    Usage:
        r = api.viewGroupPending(groupId)
        r = await api.viewGroupPendingAsync(groupId)
    """

    def _buildViewGroupPending(this, groupId):
        params = {
            "params": this._encode({
                "grid": str(groupId),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/pending-mems/list"
        return url, params

    def _parseViewGroupPending(this, data):
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

        return Group.fromDict(results, None)

    def viewGroupPending(this, groupId):
        url, params = this._buildViewGroupPending(groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseViewGroupPending(data)

    async def viewGroupPendingAsync(this, groupId):
        url, params = this._buildViewGroupPending(groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseViewGroupPending(data)