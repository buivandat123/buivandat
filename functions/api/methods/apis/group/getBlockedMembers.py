from ....index import *

class GetBlockedMembersApi:
    """
    Get blocked members in group.
    """

    def _buildGetBlockedMember(this, grid, page, count):
        return {
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grid": grid,
                "page": page,
                "count": count
            })
        }

    def _parseGetBlockedMember(this, data):
        if data.get("error_code") == 0:
            return {
                "success": True,
                "blocked_members": this._decode(data.get("data"))
            }
        return {
            "success": False,
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message", "Lỗi không xác định từ API.")
        }

    def getBlockedMembers(this, grid, page=1, count=50):
        params = this._buildGetBlockedMember(grid, page, count)
        data = this.GetSession(
            "https://tt-group-wpa.chat.zalo.me/api/group/blockedmems/list",
            params=params
        ).json()
        return this._parseGetBlockedMember(data)

    async def getBlockedMembersAsync(this, grid, page=1, count=50):
        params = this._buildGetBlockedMember(grid, page, count)
        data = await this.GetSessionAsync(
            "https://tt-group-wpa.chat.zalo.me/api/group/blockedmems/list",
            params=params
        )
        return this._parseGetBlockedMember(data)
