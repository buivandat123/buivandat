from .....index import *

class ListInviteBoxApi:
    """
    Group API: Retrieve list of invited groups (Invite Box).

    Usage:
        r = api.listInviteBox()
        r = api.listInviteBox(page=1, invPerPage=20)

        r = await api.listInviteBoxAsync()
        r = await api.listInviteBoxAsync(page=1, invPerPage=20)
    """

    def _buildListInviteBox(this, page, invPerPage, mcount, lastGroupId):
        params = {
            "zpw_ver": 664,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "mpage": 1,
                "page": int(page),
                "invPerPage": int(invPerPage),
                "mcount": int(mcount),
                "lastGroupId": lastGroupId,
                "avatar_size": 120,
                "member_avatar_size": 120
            })
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/inv-box/list"
        return url, params, payload

    def _parseListInviteBox(this, data):
        if data.get("error_code") == 0:
            return data.get("data")

        errorCode = data.get("error_code")
        errorMessage = data.get("error_message") or data.get("data")
        raise ZaloAPIException(f"Error #{errorCode} - {errorMessage}")

    def listInviteBox(this, page=0, invPerPage=12, mcount=10, lastGroupId=None):
        url, params, payload = this._buildListInviteBox(page, invPerPage, mcount, lastGroupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseListInviteBox(data)

    async def listInviteBoxAsync(this, page=0, invPerPage=12, mcount=10, lastGroupId=None):
        url, params, payload = this._buildListInviteBox(page, invPerPage, mcount, lastGroupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseListInviteBox(data)