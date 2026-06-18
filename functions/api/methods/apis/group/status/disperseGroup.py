from .....index import *

class DisperseGroupApi:
    """
    Group API: Disperse (delete) a group by ID.

    Usage:
        r = api.disperseGroup(groupId)
        r = await api.disperseGroupAsync(groupId)
    """

    def _buildDisperseGroup(this, groupId):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "grid": str(groupId),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/disperse"
        return url, params, payload

    def _parseDisperseGroup(this, data):
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

        if isinstance(results, dict) and results.get("error_code") not in (None, 0):
            raise ZaloAPIException(f"Error #{results.get('error_code')} when sending requests: {results.get('error_message') or results}")

        return Group.fromDict(results, None)

    def disperseGroup(this, groupId):
        url, params, payload = this._buildDisperseGroup(groupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseDisperseGroup(data)

    async def disperseGroupAsync(this, groupId):
        url, params, payload = this._buildDisperseGroup(groupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseDisperseGroup(data)