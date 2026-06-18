from ....index import *

class SendReactionApi:
    """
    Message API: Send reaction.

    Usage:
        api.sendReaction(messageObject, "/-ok", threadId, type, 10000020)
        await api.sendReactionAsync(messageObject, "/-ok", threadId, type, 10000020)
    """

    def _buildSendReaction(this, messageObject, reactionIcon, threadId, type, reactionType):
        params = { "zpw_ver": 647, "zpw_type": this.apiLogintype }

        msg = {
            "rMsg": [{
                "gMsgID": int(messageObject.msgId),
                "cMsgID": int(messageObject.cliMsgId),
                "msgType": utils.getClientMessageType(messageObject.msgType)
            }],
            "rIcon": reactionIcon,
            "rType": reactionType,
            "source": 6
        }

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

    def _parseSendReaction(this, data, type):
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

    def sendReaction(this, messageObject, reactionIcon, threadId, type, reactionType=75):
        url, params, payload, tType = this._buildSendReaction(
            messageObject, reactionIcon, threadId, type, reactionType
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendReaction(data, tType)

    async def sendReactionAsync(this, messageObject, reactionIcon, threadId, type, reactionType=75):
        url, params, payload, tType = this._buildSendReaction(
            messageObject, reactionIcon, threadId, type, reactionType
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendReaction(data, tType)