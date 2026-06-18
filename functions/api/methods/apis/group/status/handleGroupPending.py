from .....index import *

class HandleGroupPendingApi:
    """
    Group API: Approve / Reject pending members in group approval.

    Usage:
        r = api.handleGroupPending("uid1", groupId, isApprove=True)
        r = api.handleGroupPending(["uid1", "uid2"], groupId, isApprove=False)

        r = await api.handleGroupPendingAsync("uid1", groupId, isApprove=True)
        r = await api.handleGroupPendingAsync(["uid1", "uid2"], groupId, isApprove=False)
    """

    def _buildHandleGroupPending(this, members, groupId, isApprove):
        if isinstance(members, list):
            members = [str(x) for x in members]
        else:
            members = [str(members)]

        params = {
            "params": this._encode({
                "grid": str(groupId),
                "members": members,
                "isApprove": 1 if bool(isApprove) else 0
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/pending-mems/review"
        return url, params

    def _parseHandleGroupPending(this, data):
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

    def handleGroupPending(this, members, groupId, isApprove=True):
        url, params = this._buildHandleGroupPending(members, groupId, isApprove)
        data = this.GetSession(url, params=params).json()
        return this._parseHandleGroupPending(data)

    async def handleGroupPendingAsync(this, members, groupId, isApprove=True):
        url, params = this._buildHandleGroupPending(members, groupId, isApprove)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseHandleGroupPending(data)