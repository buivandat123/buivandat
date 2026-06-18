from .....index import *

class RemoveAdminsApi:
    """
    Group API: Remove admins in the group (white key) by ID.

    Usage:
        r = api.removeAdmins("uid1", groupId)
        r = api.removeAdmins(["uid1", "uid2"], groupId)

        r = await api.removeAdminsAsync("uid1", groupId)
        r = await api.removeAdminsAsync(["uid1", "uid2"], groupId)
    """

    def _buildRemoveAdmins(this, members, groupId):
        if isinstance(members, list):
            members = [str(x) for x in members]
        else:
            members = [str(members)]

        params = {
            "params": this._encode({
                "grid": str(groupId),
                "members": members,
                "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None)
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/admins/remove"
        return url, params

    def _parseRemoveAdmins(this, data):
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

    def removeAdmins(this, members, groupId):
        url, params = this._buildRemoveAdmins(members, groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseRemoveAdmins(data)

    async def removeAdminsAsync(this, members, groupId):
        url, params = this._buildRemoveAdmins(members, groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseRemoveAdmins(data)
