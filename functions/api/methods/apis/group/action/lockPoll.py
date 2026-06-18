from .....index import *

class LockPollApi:
    """
    Poll API: Lock / End poll by ID.

    Usage:
        r = api.lockPoll(pollId)
        r = await api.lockPollAsync(pollId)
    """

    def _buildLockPoll(this, pollId):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "poll_id": int(pollId),
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/poll/end"
        return url, params, payload

    def _parseLockPoll(this, data):
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

    def lockPoll(this, pollId):
        url, params, payload = this._buildLockPoll(pollId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseLockPoll(data)

    async def lockPollAsync(this, pollId):
        url, params, payload = this._buildLockPoll(pollId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseLockPoll(data)