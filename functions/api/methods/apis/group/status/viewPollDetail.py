from .....index import *

class ViewPollDetailApi:
    """
    Poll API: View poll detail by ID.

    Usage:
        r = api.viewPollDetail(pollId)
        r = await api.viewPollDetailAsync(pollId)
    """

    def _buildViewPollDetail(this, pollId):
        params = {
            "params": this._encode({
                "poll_id": int(pollId),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/poll/detail"
        return url, params

    def _parseViewPollDetail(this, data):
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

    def viewPollDetail(this, pollId):
        url, params = this._buildViewPollDetail(pollId)
        data = this.GetSession(url, params=params).json()
        return this._parseViewPollDetail(data)

    async def viewPollDetailAsync(this, pollId):
        url, params = this._buildViewPollDetail(pollId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseViewPollDetail(data)