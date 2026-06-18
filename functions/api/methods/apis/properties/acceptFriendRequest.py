from ....index import *

class AcceptFriendRequestApi:
    """
    Friend API: Accept friend request from user by ID.

    Usage:
        r = api.acceptFriendRequest(userId)
        r = api.acceptFriendRequest(userId, language="vi")

        r = await api.acceptFriendRequestAsync(userId)
        r = await api.acceptFriendRequestAsync(userId, language="vi")
    """

    def _buildAcceptFriendRequest(this, userId, language):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "fid": str(userId),
                "language": language
            })
        }

        url = "https://tt-friend-wpa.chat.zalo.me/api/friend/accept"
        return url, params, payload

    def _parseAcceptFriendRequest(this, data):
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

    def acceptFriendRequest(this, userId, language="en"):
        url, params, payload = this._buildAcceptFriendRequest(userId, language)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseAcceptFriendRequest(data)

    async def acceptFriendRequestAsync(this, userId, language="en"):
        url, params, payload = this._buildAcceptFriendRequest(userId, language)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseAcceptFriendRequest(data)