from ....index import *

class ChangeGroupOwnerApi:
    """
    Group API: Change group owner (yellow key) by ID.

    Usage:
        r = api.changeGroupOwner(newAdminId, groupId)
        r = await api.changeGroupOwnerAsync(newAdminId, groupId)
    """

    def _buildChangeGroupOwner(this, newAdminId, groupId):
        params = {
            "params": this._encode({
                "grid": str(groupId),
                "newAdminId": str(newAdminId),
                "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None),
                "language": "vi"
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/change-owner"
        return url, params

    def _parseChangeGroupOwner(this, data):
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

    def changeGroupOwner(this, newAdminId, groupId):
        url, params = this._buildChangeGroupOwner(newAdminId, groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseChangeGroupOwner(data)

    async def changeGroupOwnerAsync(this, newAdminId, groupId):
        url, params = this._buildChangeGroupOwner(newAdminId, groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseChangeGroupOwner(data)