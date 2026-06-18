from ....index import *

class UnfriendUserApi:
    """
    Friend API: Unfriend a user by ID.

    Usage:
        r = api.unfriendUser(userId)
        r = api.unfriendUser(userId, language="en")

        r = await api.unfriendUserAsync(userId)
        r = await api.unfriendUserAsync(userId, language="en")
    """

    def _buildUnfriendUser(this, userId, language):
        params = {
            "zpw_ver": 641,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "fid": str(userId),
                "language": language
            })
        }

        url = "https://tt-friend-wpa.chat.zalo.me/api/friend/remove"
        return url, params, payload

    def _parseUnfriendUser(this, data):
        if data.get("error_code") == 0:
            return {
                "status": "success",
                "message": "Unfriended successfully."
            }

        errorCode = data.get("error_code")
        errorMessage = data.get("error_message") or data.get("data")
        raise ZaloAPIException(f"Error #{errorCode} when unfriending: {errorMessage}")

    def unfriendUser(this, userId, language="en"):
        url, params, payload = this._buildUnfriendUser(userId, language)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseUnfriendUser(data)

    async def unfriendUserAsync(this, userId, language="en"):
        url, params, payload = this._buildUnfriendUser(userId, language)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseUnfriendUser(data)