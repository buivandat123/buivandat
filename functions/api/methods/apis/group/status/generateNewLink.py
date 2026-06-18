from .....index import *

class GenerateNewLinkApi:
    """
    Group API: Generate a new invite link for a group.

    Usage:
        r = api.generateNewLink(groupId)
        r = await api.generateNewLinkAsync(groupId)

    Returns:
        dict:
            {
                "success": True,
                "new_link": "<invite_link>"
            }

            or

            {
                "success": False,
                "error_code": int,
                "error_message": str
            }
    """

    def _buildGenerateNewLink(this, grid):
        params = {
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "grid": str(grid)
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/link/new"
        return url, params

    def _parseGenerateNewLink(this, data):
        if data.get("error_code") != 0:
            return {
                "success": False,
                "error_code": data.get("error_code"),
                "error_message": data.get("error_message") or "Unknown API error"
            }

        raw = data.get("data")
        if not raw:
            return {
                "success": False,
                "error_code": 1337,
                "error_message": "Data is None"
            }

        decoded = this._decode(raw)
        link = decoded.get("link") if isinstance(decoded, dict) else None

        if not link:
            return {
                "success": False,
                "error_code": 1337,
                "error_message": ""
            }

        return {
            "success": True,
            "new_link": link
        }

    def generateNewLink(this, grid):
        url, params = this._buildGenerateNewLink(grid)
        data = this.PostSession(url, data=params).json()
        return this._parseGenerateNewLink(data)

    async def generateNewLinkAsync(this, grid):
        url, params = this._buildGenerateNewLink(grid)
        data = await this.PostSessionAsync(url, data=params)
        return this._parseGenerateNewLink(data)