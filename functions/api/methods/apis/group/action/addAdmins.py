from .....index import *

class AddAdminsApi:
    """
    Group API: Add admins to the group (white key).

    Usage:
        r = api.addAdmins("uid1", groupId)
        r = api.addAdmins(["uid1", "uid2"], groupId)

        r = await api.addAdminsAsync("uid1", groupId)
        r = await api.addAdminsAsync(["uid1", "uid2"], groupId)
    """

    def _buildAddAdmins(this, members, groupId):
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

        url = "https://tt-group-wpa.chat.zalo.me/api/group/admins/add"
        return url, params

    def _parseAddAdmins(this, data):
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

    def addAdmins(this, members, groupId):
        url, params = this._buildAddAdmins(members, groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseAddAdmins(data)

    async def addAdminsAsync(this, members, groupId):
        url, params = this._buildAddAdmins(members, groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseAddAdmins(data)
