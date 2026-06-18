from ....index import *

class CheckGroupApi:
    """
    Get group information by invite link.

    Usage:
        api.checkGroup(link)
        await api.checkGroupAsync(link)
    """

    def _buildCheckGroup(this, link):
        params = {
            "params": this._encode({
                "link": link,
                "avatar_size": 120,
                "member_avatar_size": 120,
                "mpage": 1
            }),
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype
        }
        return params

    def _parseCheckGroup(this, data):
        if data.get("error_code") == 0:
            d = this._decode(data.get("data"))
            return d.get("data") if d and d.get("data") else {
                "error_code": 1337,
                "error_message": "Không tìm thấy dữ liệu nhóm."
            }
        return {
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message", "Lỗi không xác định từ API.")
        }

    def checkGroup(this, link):
        params = this._buildCheckGroup(link)
        data = this.GetSession(
            "https://tt-group-wpa.chat.zalo.me/api/group/link/ginfo",
            params=params
        ).json()
        return this._parseCheckGroup(data)

    async def checkGroupAsync(this, link):
        params = this._buildCheckGroup(link)
        data = await this.GetSessionAsync(
            "https://tt-group-wpa.chat.zalo.me/api/group/link/ginfo",
            params=params
        )
        return this._parseCheckGroup(data)
