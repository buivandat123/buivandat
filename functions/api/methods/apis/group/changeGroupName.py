from ....index import *

class ChangeGroupNameApi:
    """
    Group API: Set/Change group name by ID.

    Usage:
        r = api.changeGroupName("New Name", groupId)
        r = await api.changeGroupNameAsync("New Name", groupId)
    """

    def _buildChangeGroupName(this, groupName, groupId):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "gname": groupName,
                "grid": str(groupId)
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/updateinfo"
        return url, params, payload

    def _parseChangeGroupName(this, data):
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

    def changeGroupName(this, groupName, groupId):
        url, params, payload = this._buildChangeGroupName(groupName, groupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseChangeGroupName(data)

    async def changeGroupNameAsync(this, groupName, groupId):
        url, params, payload = this._buildChangeGroupName(groupName, groupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseChangeGroupName(data)