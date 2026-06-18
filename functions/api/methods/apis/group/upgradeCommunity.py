from ....index import *

class UpgradeCommunityApi:
    """
    Group API: Upgrade group to community.

    Usage:
        r = api.upgradeCommunity(groupId)
        r = await api.upgradeCommunityAsync(groupId)
    """

    def _buildUpgradeCommunity(this, groupId):
        params = {
            "zpw_ver": 655,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grId": str(groupId),
                "language": "vi"
            })
        }
        url = "https://tt-group-wpa.chat.zalo.me/api/group/upgrade/community"
        return url, params

    def _parseUpgradeCommunity(this, data):
        if data.get("error_code") == 0:
            results = data.get("data")
            if not results:
                raise ZaloAPIException("Error #1337 when sending requests: Data is None")
            results = this._decode(results)
            return Group.fromDict(results, None)

        errorCode = data.get("error_code")
        errorMessage = data.get("error_message") or data.get("data")
        raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

    def upgradeCommunity(this, groupId):
        url, params = this._buildUpgradeCommunity(groupId)
        data = this.GetSession(url, params=params).json()
        return this._parseUpgradeCommunity(data)

    async def upgradeCommunityAsync(this, groupId):
        url, params = this._buildUpgradeCommunity(groupId)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseUpgradeCommunity(data)