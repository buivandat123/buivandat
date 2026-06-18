from .....index import *

class DisableGroupLinkApi:
    """
    Group API: Disable group invite link.

    Usage:
        r = api.disableLink(groupId)
        r = await api.disableLinkAsync(groupId)

    Returns:
        dict:
            { "success": True, "message": str }

            or

            { "success": False, "error_code": int, "error_message": str }
    """

    def _buildDisableLink(this, grid):
        params = {
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grid": str(grid)
            })
        }
        url = "https://tt-group-wpa.chat.zalo.me/api/group/link/disable"
        return url, params

    def _parseDisableLink(this, data):
        if data.get("error_code") == 0:
            return {
                "success": True,
                "message": "Đã vô hiệu hóa liên kết nhóm thành công."
            }

        return {
            "success": False,
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message") or "Unknown API error"
        }

    def disableLink(this, grid):
        url, params = this._buildDisableLink(grid)
        data = this.PostSession(url, data=params).json()
        return this._parseDisableLink(data)

    async def disableLinkAsync(this, grid):
        url, params = this._buildDisableLink(grid)
        data = await this.PostSessionAsync(url, data=params)
        return this._parseDisableLink(data)