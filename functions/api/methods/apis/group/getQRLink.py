from ....index import *

class GetQRLinkApi:
    """
    Get QR link of a user.

    Usage:
        api.getQRLink(userId)
        await api.getQRLinkAsync(userId)
    """

    def _buildGetQRLink(this, userId):
        return (
            {"zpw_ver": 641, "zpw_type": this.apiLogintype},
            {"params": this._encode({"fids": [str(userId)]})}
        )

    def _parseGetQRLink(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if isinstance(r, dict) and r.get("data") else r
            return r
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def getQRLink(this, userId):
        params, payload = this._buildGetQRLink(userId)
        data = this.PostSession(
            "https://tt-friend-wpa.chat.zalo.me/api/friend/mget-qr",
            params=params,
            data=payload
        ).json()
        return this._parseGetQRLink(data)

    async def getQRLinkAsync(this, userId):
        params, payload = this._buildGetQRLink(userId)
        data = await this.PostSessionAsync(
            "https://tt-friend-wpa.chat.zalo.me/api/friend/mget-qr",
            params=params,
            data=payload
        )
        return this._parseGetQRLink(data)