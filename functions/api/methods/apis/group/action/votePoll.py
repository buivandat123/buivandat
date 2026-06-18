from .....index import *

class VotePollApi:
    """
    Poll API: Vote poll by ID.

    Usage:
        r = api.votePoll(pollId, optionIds)
        r = api.votePoll(pollId, [1, 2])
        r = api.votePoll(pollId, optionIds, groupId=groupId)

        r = await api.votePollAsync(pollId, optionIds)
        r = await api.votePollAsync(pollId, [1, 2], groupId=groupId)
    """

    def _buildVotePoll(this, pollId, optionIds, groupId):
        params = {
            "zpw_ver": 677,
            "zpw_type": this.apiLogintype
        }

        if isinstance(optionIds, (list, tuple, set)):
            optionIds = [int(x) for x in optionIds]
        else:
            optionIds = [int(optionIds)]

        p = {
            "poll_id": int(pollId),
            "option_ids": optionIds,
            "imei": getattr(this, "_imei", None)
                    or getattr(getattr(this, "_state", None), "clientUUID", None)
        }

        if groupId is not None:
            p["group_id"] = str(groupId)

        payload = { "params": this._encode(p) }
        url = "https://tt-group-wpa.chat.zalo.me/api/poll/vote"
        return url, params, payload

    def _parseVotePoll(this, data):
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
                return json.loads(results)
            except:
                return { "error_code": 1337, "error_message": results }

        return results

    def votePoll(this, pollId, optionIds, groupId=None):
        url, params, payload = this._buildVotePoll(pollId, optionIds, groupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseVotePoll(data)

    async def votePollAsync(this, pollId, optionIds, groupId=None):
        url, params, payload = this._buildVotePoll(pollId, optionIds, groupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseVotePoll(data)
