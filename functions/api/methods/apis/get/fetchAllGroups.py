from ....index import *

class FetchAllGroupsApi:
    """
    Fetch all group IDs the client is participating in.
    """

    def _buildFetchAllGroup(this):
        return {"zpw_ver": 645, "zpw_type": this.apiLogintype}

    def _parseFetchAllGroup(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("error_code") == 0 else r
            return Group.fromDict(r or {}, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def fetchAllGroups(this):
        params = this._buildFetchAllGroup()
        data = this.GetSession(
            "https://tt-group-wpa.chat.zalo.me/api/group/getlg/v4",
            params=params
        ).json()
        return this._parseFetchAllGroup(data)

    async def fetchAllGroupsAsync(this):
        params = this._buildFetchAllGroup()
        data = await this.GetSessionAsync(
            "https://tt-group-wpa.chat.zalo.me/api/group/getlg/v4",
            params=params
        )
        return this._parseFetchAllGroup(data)