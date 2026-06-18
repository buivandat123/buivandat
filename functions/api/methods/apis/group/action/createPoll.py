from .....index import *

class CreatePollApi:
    """
    Poll API: Create poll in group by ID.

    Usage:
        r = api.createPoll(
            question="Ăn gì tối nay?",
            options=["Bún", "Phở", "Cơm"],
            groupId=groupId,
            expiredTime=0,
            pinAct=False,
            multiChoices=True,
            allowAddNewOption=True,
            hideVotePreview=False,
            isAnonymous=False
        )

        r = await api.createPollAsync(
            question="Đi đâu cuối tuần?",
            options=["Cafe", "Xem phim"],
            groupId=groupId,
            pinAct=True
        )
    """

    def _buildCreatePoll(this, question, options, groupId, expiredTime, pinAct, multiChoices, allowAddNewOption, hideVotePreview, isAnonymous):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        if isinstance(options, list):
            opt = [str(x) for x in options]
        else:
            opt = [str(options)]

        p = {
            "group_id": str(groupId),
            "question": str(question),
            "options": opt,
            "expired_time": int(expiredTime or 0),
            "pinAct": bool(pinAct),
            "allow_multi_choices": bool(multiChoices),
            "allow_add_new_option": bool(allowAddNewOption),
            "is_hide_vote_preview": bool(hideVotePreview),
            "is_anonymous": bool(isAnonymous),
            "poll_type": 0,
            "src": 1,
            "imei": getattr(this, "_imei", None)
                    or getattr(getattr(this, "_state", None), "clientUUID", None)
        }

        payload = { "params": this._encode(p) }
        url = "https://tt-group-wpa.chat.zalo.me/api/poll/create"
        return url, params, payload

    def _parseCreatePoll(this, data):
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

    def createPoll(this, question, options, groupId, expiredTime=0, pinAct=False, multiChoices=True, allowAddNewOption=True, hideVotePreview=False, isAnonymous=False):
        url, params, payload = this._buildCreatePoll(
            question, options, groupId, expiredTime, pinAct, multiChoices, allowAddNewOption, hideVotePreview, isAnonymous
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseCreatePoll(data)

    async def createPollAsync(this, question, options, groupId, expiredTime=0, pinAct=False, multiChoices=True, allowAddNewOption=True, hideVotePreview=False, isAnonymous=False):
        url, params, payload = this._buildCreatePoll(
            question, options, groupId, expiredTime, pinAct, multiChoices, allowAddNewOption, hideVotePreview, isAnonymous
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseCreatePoll(data)