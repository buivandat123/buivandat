from ....index import *

class BlockViewFeedApi:
    """
    Friend API: Block / Unblock friend view feed by ID.

    Usage:
        r = api.blockViewFeed(userId, True)
        r = api.blockViewFeed(userId, False)

        r = await api.blockViewFeedAsync(userId, True)
        r = await api.blockViewFeedAsync(userId, False)
    """

    def _buildBlockViewFeed(this, userId, isBlockFeed):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "fid": str(userId),
                "isBlockFeed": 1 if bool(isBlockFeed) else 0,
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-friend-wpa.chat.zalo.me/api/friend/feed/block"
        return url, params, payload

    def _parseBlockViewFeed(this, data):
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

        return User.fromDict(results, None)

    def blockViewFeed(this, userId, isBlockFeed=True):
        url, params, payload = this._buildBlockViewFeed(userId, isBlockFeed)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseBlockViewFeed(data)

    async def blockViewFeedAsync(this, userId, isBlockFeed=True):
        url, params, payload = this._buildBlockViewFeed(userId, isBlockFeed)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseBlockViewFeed(data)