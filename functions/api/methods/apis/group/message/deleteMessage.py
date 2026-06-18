from .....index import *

class DeleteMessageApi:
    """
    Group API: Delete message in group by ID.

    Usage:
        r = api.deleteMessage(msgId, ownerId, clientMsgId, groupId, onlyMe=False)
        r = await api.deleteMessageAsync(msgId, ownerId, clientMsgId, groupId, onlyMe=False)
    """

    def buildDeleteMessage(this, msgId, ownerId, clientMsgId, groupId, onlyMe=False):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "grid": str(groupId),
                "cliMsgId": utils.now(),
                "msgs": [{
                    "cliMsgId": str(clientMsgId),
                    "globalMsgId": str(msgId),
                    "ownerId": str(ownerId),
                    "destId": str(groupId)
                }],
                "onlyMe": 1 if onlyMe else 0
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/deletemsg"
        return url, params, payload

    def parseDeleteMessage(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        results = this._decode(results)
        if isinstance(results, dict) and results.get("data"):
            results = results["data"]

        if results is None:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                raise ZaloAPIException(f"Error #1337 when sending requests: {results}")

        return Group.fromDict(results, None)

    def deleteMessage(this, msgId, ownerId, clientMsgId, groupId, onlyMe=False):
        url, params, payload = this.buildDeleteMessage(msgId, ownerId, clientMsgId, groupId, onlyMe)
        data = this.PostSession(url, params=params, data=payload).json()
        return this.parseDeleteMessage(data)

    async def deleteMessageAsync(this, msgId, ownerId, clientMsgId, groupId, onlyMe=False):
        url, params, payload = this.buildDeleteMessage(msgId, ownerId, clientMsgId, groupId, onlyMe)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this.parseDeleteMessage(data)