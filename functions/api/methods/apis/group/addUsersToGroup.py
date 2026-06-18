from ....index import *

class AddUsersToGroupApi:
    """
    Group API: Add friends/users to a group.

    Usage:
        r = api.addUsersToGroup(["uid1", "uid2"], groupId)
        r = api.addUsersToGroup("uid1", groupId)

        r = await api.addUsersToGroupAsync(["uid1", "uid2"], groupId)
        r = await api.addUsersToGroupAsync("uid1", groupId)
    """

    def _buildAddUsersToGroup(this, userIds, groupId):
        if userIds and isinstance(userIds, list):
            members = [str(x) for x in userIds]
        else:
            members = [str(userIds)] if userIds else []

        memberTypes = [-1] * len(members)

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "grid": str(groupId),
                "members": members,
                "memberTypes": memberTypes,
                "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None),
                "clientLang": "vi"
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/invite/v2"
        return url, params, payload

    def _parseAddUsersToGroup(this, data):
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

    def addUsersToGroup(this, user_ids, groupId):
        url, params, payload = this._buildAddUsersToGroup(user_ids, groupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseAddUsersToGroup(data)

    async def addUsersToGroupAsync(this, user_ids, groupId):
        url, params, payload = this._buildAddUsersToGroup(user_ids, groupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseAddUsersToGroup(data)