from ....index import *

class GetRecentGroupApi:
    """
    Get recent messages in a group.
    """

    def _buildgetRecentGroup(this, groupId):
        return {
            "params": this._encode({
                "groupId": str(groupId),
                "globalMsgId": 10**16,
                "count": 50,
                "msgIds": [],
                "imei": this._imei,
                "src": 1
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "nretry": 0
        }

    def _parsegetRecentGroup(this, data):
        if data.get("error_code") == 0:
            r = this._decode(data.get("data"))
            return Group.fromDict(json.loads(r.get("data")), None)
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def getRecentGroup(this, groupId):
        params = this._buildgetRecentGroup(groupId)
        data = this.GetSession(
            "https://tt-group-cm.chat.zalo.me/api/cm/getrecentv2",
            params=params
        ).json()
        return this._parsegetRecentGroup(data)

    async def getRecentGroupAsync(this, groupId):
        params = this._buildgetRecentGroup(groupId)
        data = await this.GetSessionAsync(
            "https://tt-group-cm.chat.zalo.me/api/cm/getrecentv2",
            params=params
        )
        return this._parsegetRecentGroup(data)
