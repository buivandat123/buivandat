from ....index import *

class SendFriendRequestApi:
    """
    Friend API: Send friend request to a user by ID.

    Usage:
        r = api.addFriend(userId, "Hello")
        r = api.addFriend(userId, "Hello", language="en")

        r = await api.addFriendAsync(userId, "Hello")
        r = await api.addFriendAsync(userId, "Hello", language="en")
    """

    def _buildSendFriendRequest(this, userId, msg, language):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "toid": str(userId),
                "msg": str(msg),
                "reqsrc": 30,
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None),
                "language": language,
                "srcParams": json.dumps({
                    "uidTo": str(userId)
                })
            })
        }

        url = "https://tt-friend-wpa.chat.zalo.me/api/friend/sendreq"
        return url, params, payload

    def _parseSendFriendRequest(this, data):
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

    def addFriend(this, userId, msg, language="en"):
        url, params, payload = this._buildSendFriendRequest(userId, msg, language)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendFriendRequest(data)

    async def addFriendAsync(this, userId, msg, language="en"):
        url, params, payload = this._buildSendFriendRequest(userId, msg, language)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendFriendRequest(data)