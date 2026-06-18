from ....index import *

class SendMultiReactionApi:
    """
    Message API: Send multi reaction (repeat rMsg numreact times for same message).

    Usage:
        api.sendMultiReaction(messageObject, "👍", threadId, type, numreact=3)
        await api.sendMultiReactionAsync(messageObject, "👍", threadId, type, numreact=3)
    """

    def _buildSendMultiReaction(this, messageObject, reactionIcon, threadId, type, reactionType, numreact):
        if not hasattr(messageObject, "msgId") or not hasattr(messageObject, "cliMsgId") or not hasattr(messageObject, "msgType"):
            raise ZaloUserError("Reaction type is invalid")

        try:
            numreact = int(numreact or 1)
        except Exception:
            numreact = 1
        if numreact < 1:
            numreact = 1

        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype }

        msg = {
            "rMsg": [],
            "rIcon": reactionIcon,
            "rType": reactionType,
            "source": 6
        }

        rMsgItem = {
            "gMsgID": int(messageObject.msgId),
            "cMsgID": int(messageObject.cliMsgId),
            "msgType": utils.getClientMessageType(messageObject.msgType)
        }

        msg["rMsg"] = [rMsgItem] * numreact

        payloadParams = {
            "react_list": [{
                "message": json.dumps(msg),
                "clientId": utils.now()
            }],
            "imei": this._imei
        }

        if type == ThreadType.USER:
            url = "https://reaction.chat.zalo.me/api/message/reaction"
            payloadParams["toid"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://reaction.chat.zalo.me/api/group/reaction"
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, type

    def _parseSendMultiReaction(this, data, type):
        if data.get("error_code") == 0:
            results = data.get("data")
            if not results:
                raise ZaloAPIException("Error #1337 when sending requests: Data is None")

            results = this._decode(results)
            results = results.get("data") or results

            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except Exception:
                    raise ZaloAPIException(f"Error #1337 when sending requests: {results}")

            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )

    def sendMultiReaction(this, messageObject, reactionIcon, threadId, type, reactionType=75, numreact=1):
        url, params, payload, tType = this._buildSendMultiReaction(
            messageObject, reactionIcon, threadId, type, reactionType, numreact
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendMultiReaction(data, tType)

    async def sendMultiReactionAsync(this, messageObject, reactionIcon, threadId, type, reactionType=75, numreact=1):
        url, params, payload, tType = this._buildSendMultiReaction(
            messageObject, reactionIcon, threadId, type, reactionType, numreact
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendMultiReaction(data, tType)