from .....index import *

class UnblockUsersApi:
    """
    Group API: Unblock members in a group.

    Usage:
        r = api.unblockUsers("uid1", groupId)
        r = api.unblockUsers(["uid1", "uid2"], groupId)

        r = await api.unblockUsersAsync("uid1", groupId)
        r = await api.unblockUsersAsync(["uid1", "uid2"], groupId)
    """

    def _buildUnblockUsers(this, members, groupId):
        if isinstance(members, list):
            members = [str(x) for x in members]
        else:
            members = [str(members)]

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grid": str(groupId),
                "members": members
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/blockedmems/remove"
        return url, params

    def _parseUnblockUsers(this, data):
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

    def unblockUsers(this, members, groupId):
        url, params = this._buildUnblockUsers(members, groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseUnblockUsers(data)

    async def unblockUsersAsync(this, members, groupId):
        url, params = this._buildUnblockUsers(members, groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseUnblockUsers(data)