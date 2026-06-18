from .....index import *

class KickUsersApi:
    """
    Group API: Kick members out of a group.

    Usage:
        r = api.kickUsers("uid1", groupId)
        r = api.kickUsers(["uid1", "uid2"], groupId)

        r = await api.kickUsersAsync("uid1", groupId)
        r = await api.kickUsersAsync(["uid1", "uid2"], groupId)
    """

    def _buildKickUsers(this, members, groupId):
        if isinstance(members, list):
            members = [str(x) for x in members]
        else:
            members = [str(members)]

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "grid": str(groupId),
                "members": members
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/kickout"
        return url, params, payload

    def _parseKickUsers(this, data):
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

    def kickUsers(this, members, groupId):
        url, params, payload = this._buildKickUsers(members, groupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseKickUsers(data)

    async def kickUsersAsync(this, members, groupId):
        url, params, payload = this._buildKickUsers(members, groupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseKickUsers(data)
