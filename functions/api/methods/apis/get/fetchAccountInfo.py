from ....index import *

class FetchAccountInfoApi:
    """
    Fetch current client account information.

    Usage:
        api.fetchAccountInfo()
        await api.fetchAccountInfoAsync()
    """

    def _buildFetchAccountInfo(this):
        return {
            "params": this._encode({
                "avatar_size": 120,
                "imei": this._imei
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "os": 8,
            "browser": 0
        }

    def _parseFetchAccountInfo(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("error_code") == 0 else r
            return User.fromDict(r or {}, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def fetchAccountInfo(this):
        params = this._buildFetchAccountInfo()
        data = this.GetSession(
            "https://tt-profile-wpa.chat.zalo.me/api/social/profile/me-v2",
            params=params
        ).json()
        return this._parseFetchAccountInfo(data)

    async def fetchAccountInfoAsync(this):
        params = this._buildFetchAccountInfo()
        data = await this.GetSessionAsync(
            "https://tt-profile-wpa.chat.zalo.me/api/social/profile/me-v2",
            params=params
        )
        return this._parseFetchAccountInfo(data)