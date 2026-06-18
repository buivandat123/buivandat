from .....index import *

class BoxInviteAcceptApi:
    """
    Group API: Accept an invitation from Invite Box.

    Usage:
        r = api.boxInviteAccept(groupId)
        r = api.boxInviteAccept(groupId, lang="en")

        r = await api.boxInviteAcceptAsync(groupId)
        r = await api.boxInviteAcceptAsync(groupId, lang="en")
    """

    def _buildBoxInviteAccept(this, groupId, lang):
        params = {
            "zpw_ver": 664,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "grid": int(groupId),
                "lang": lang
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/inv-box/join"
        return url, params, payload

    def _parseBoxInviteAccept(this, data):
        if data.get("error_code") == 0:
            return data.get("data")

        errorCode = data.get("error_code")
        errorMessage = data.get("error_message") or data.get("data")
        raise ZaloAPIException(f"Error #{errorCode} - {errorMessage}")

    def boxInviteAccept(this, groupId, lang="en"):
        url, params, payload = this._buildBoxInviteAccept(groupId, lang)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseBoxInviteAccept(data)

    async def boxInviteAcceptAsync(this, groupId, lang="en"):
        url, params, payload = this._buildBoxInviteAccept(groupId, lang)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseBoxInviteAccept(data)