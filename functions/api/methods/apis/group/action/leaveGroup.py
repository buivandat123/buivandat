from .....index import *

class LeaveGroupApi:
    """
    Group API: Leave group by ID.

    Usage:
        r = api.leaveGroup(groupId, silent=True)
        r = api.leaveGroup(groupId, silent=False)

        r = await api.leaveGroupAsync(groupId, silent=True)
        r = await api.leaveGroupAsync(groupId, silent=False)
    """

    def _buildLeaveGroup(this, groupId, silent):
        if not groupId:
            raise ZaloAPIException("Missing Group ID")

        params = {
            "zpw_ver": 648,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "grids": [str(groupId)],
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None),
                "silent": 1 if bool(silent) else 0
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/leave"
        return url, params, payload

    def _parseLeaveGroup(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            return { "error_code": 1337, "error_message": "Data is None" }

        results = this._decode(results)
        results = results.get("data") if isinstance(results, dict) and results.get("data") else results

        if results is None:
            return { "error_code": 1337, "error_message": "Data is None" }

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                return { "error_code": 1337, "error_message": results }

        return results

    def leaveGroup(this, gr_id, silent=True):
        url, params, payload = this._buildLeaveGroup(gr_id, silent)
        data = this.PostSession(url=url, params=params, data=payload).json()
        return this._parseLeaveGroup(data)

    async def leaveGroupAsync(this, gr_id, silent=True):
        url, params, payload = this._buildLeaveGroup(gr_id, silent)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseLeaveGroup(data)