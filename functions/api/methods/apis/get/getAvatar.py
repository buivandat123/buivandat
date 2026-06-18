from ....index import *

class GetAvatarApi:
    def _buildGetAvatar(this, userId, avatarSize=120):
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}
        p = {"fid": str(userId), "imei": this._imei, "avatar_size": int(avatarSize)}
        return params, {"params": this._encode(p)}

    def _parseGetAvatar(this, data):
        if data.get("error_code") == 0:
            d = data.get("data")
            if isinstance(d, str):
                r = this._decode(d) or {}
                if r.get("error_code") == 0:
                    return r.get("data") or {}
                return r
            if isinstance(d, dict):
                return d
            return {}

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def getAvatar(this, userId, avatarSize=120):
        params, payload = this._buildGetAvatar(userId, avatarSize)
        data = this.PostSession(
            "https://tt-profile-wpa.chat.zalo.me/api/social/profile/avatar",
            params=params,
            data=payload
        ).json()
        return this._parseGetAvatar(data)

    async def getAvatarAsync(this, userId, avatarSize=120):
        params, payload = this._buildGetAvatar(userId, avatarSize)
        data = await this.PostSessionAsync(
            "https://tt-profile-wpa.chat.zalo.me/api/social/profile/avatar",
            params=params,
            data=payload
        )
        return this._parseGetAvatar(data)