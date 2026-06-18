from ....index import *

class UndoMessageApi:
    """
    Message API: Undo message by ID.

    Usage:
        r = api.undoMessage(msgId, cliMsgId, threadId, ThreadType.USER)
        r = api.undoMessage(msgId, cliMsgId, threadId, ThreadType.GROUP)

        r = await api.undoMessageAsync(msgId, cliMsgId, threadId, ThreadType.USER)
        r = await api.undoMessageAsync(msgId, cliMsgId, threadId, ThreadType.GROUP)
    """

    def _buildUndoMessage(this, msgId, cliMsgId, threadId, tType):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "nretry": 0
        }

        p = {
            "msgId": str(msgId),
            "cliMsgIdUndo": str(cliMsgId),
            "clientId": utils.now()
        }

        if tType == ThreadType.USER:
            url = "https://tt-chat3-wpa.chat.zalo.me/api/message/undo"
            p["toid"] = str(threadId)
        elif tType == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/undomsg"
            p["grid"] = str(threadId)
            p["visibility"] = 0
            p["imei"] = getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(p) }
        return url, params, payload, tType

    def _parseUndoMessage(this, data, tType):
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

        return Group.fromDict(results, None) if tType == ThreadType.GROUP else User.fromDict(results, None)

    def undoMessage(this, msgId, cliMsgId, threadId, type):
        url, params, payload, tType = this._buildUndoMessage(msgId, cliMsgId, threadId, type)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseUndoMessage(data, tType)

    async def undoMessageAsync(this, msgId, cliMsgId, threadId, type):
        url, params, payload, tType = this._buildUndoMessage(msgId, cliMsgId, threadId, type)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseUndoMessage(data, tType)