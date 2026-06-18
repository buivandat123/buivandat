from ....index import *

class GetLastMsgsApi:
    """
    Get last messages of all conversations.
    """

    def _buildGetLastMsgs(this):
        return {
            "zpw_ver": "645",
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "threadIdLocalMsgId": json.dumps({}),
                "imei": this._imei
            })
        }

    def _parseGetLastMsgs(this, data):
        if data.get("error_code") == 0:
            r = this._decode(data.get("data"))
            return User.fromDict(r.get("data"), None)
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def getLastMsgs(this):
        params = this._buildGetLastMsgs()
        data = this.GetSession(
            "https://tt-convers-wpa.chat.zalo.me/api/preloadconvers/get-last-msgs",
            params=params
        ).json()
        return this._parseGetLastMsgs(data)

    async def getLastMsgsAsync(this):
        params = this._buildGetLastMsgs()
        data = await this.GetSessionAsync(
            "https://tt-convers-wpa.chat.zalo.me/api/preloadconvers/get-last-msgs",
            params=params
        )
        return this._parseGetLastMsgs(data)
