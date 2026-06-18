from .....index import *

class UnpinMessageApi:
    """
    Group API: Unpin message in group by ID.

    Usage:
        r = api.unpinMessage(pinId, pinTime, groupId)
        r = await api.unpinMessageAsync(pinId, pinTime, groupId)
    """

    def _buildUnpinMessage(this, pinId, pinTime, groupId):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grid": str(groupId),
                "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None),
                "topic": {
                    "topicId": str(pinId),
                    "topicType": 2
                },
                "boardVersion": int(pinTime)
            })
        }

        url = "https://groupboard-wpa.chat.zalo.me/api/board/unpinv2"
        return url, params

    def _parseUnpinMessage(this, data):
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

    def unpinMessage(this, pinId, pinTime, groupId):
        url, params = this._buildUnpinMessage(pinId, pinTime, groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseUnpinMessage(data)

    async def unpinMessageAsync(this, pinId, pinTime, groupId):
        url, params = this._buildUnpinMessage(pinId, pinTime, groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseUnpinMessage(data)