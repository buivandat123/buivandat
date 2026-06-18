from ....index import *

class FetchUserInfoApi:
    """
    Fetch user information by user ID(s).
    """

    def _buildFetchUserInfo(this, userId):
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}

        p = {
            "phonebook_version": int(utils.now() / 1000),
            "friend_pversion_map": [],
            "avatar_size": 120,
            "language": "vi",
            "show_online_status": 1,
            "imei": this._imei
        }

        if isinstance(userId, list):
            p["friend_pversion_map"] = [str(i) + "_0" for i in userId]
        else:
            p["friend_pversion_map"].append(str(userId) + "_0")

        return params, {"params": this._encode(p)}

    def _parseFetchUserInfo(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("error_code") == 0 else r
            return User.fromDict(r or {}, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def fetchUserInfo(this, userId):
        params, payload = this._buildFetchUserInfo(userId)
        data = this.PostSession(
            "https://tt-profile-wpa.chat.zalo.me/api/social/friend/getprofiles/v2",
            params=params,
            data=payload
        ).json()
        return this._parseFetchUserInfo(data)

    async def fetchUserInfoAsync(this, userId):
        params, payload = this._buildFetchUserInfo(userId)
        data = await this.PostSessionAsync(
            "https://tt-profile-wpa.chat.zalo.me/api/social/friend/getprofiles/v2",
            params=params,
            data=payload
        )
        return this._parseFetchUserInfo(data)