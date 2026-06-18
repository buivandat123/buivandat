from ....index import *

class FetchAllFriendsApi:
    """
    Fetch all friend IDs of the client.
    """

    def _buildFetchAllFriends(this):
        return {
            "params": this._encode({
                "incInvalid": 0,
                "page": 1,
                "count": 20000,
                "avatar_size": 120,
                "actiontime": 0
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "nretry": 0
        }

    def _parseFetchAllFriends(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            return [User(**i) for i in (r.get("data") or [])]

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def fetchAllFriends(this):
        params = this._buildFetchAllFriends()
        data = this.GetSession(
            "https://profile-wpa.chat.zalo.me/api/social/friend/getfriends",
            params=params
        ).json()
        return this._parseFetchAllFriends(data)

    async def fetchAllFriendsAsync(this):
        params = this._buildFetchAllFriends()
        data = await this.GetSessionAsync(
            "https://profile-wpa.chat.zalo.me/api/social/friend/getfriends",
            params=params
        )
        return this._parseFetchAllFriends(data)