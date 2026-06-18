from ....index import *

class FetchGroupInfoApi:
    """
    Fetch group information by group ID(s).
    """

    def _buildFetchGroupInfo(this, groupId):
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}
        m = {}

        if isinstance(groupId, dict):
            for i in groupId:
                m[str(i)] = 0
        else:
            m[str(groupId)] = 0

        payload = {
            "params": this._encode({
                "gridVerMap": json.dumps(m)
            })
        }

        return params, payload

    def _parseFetchGroupInfo(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("error_code") == 0 else r
            return Group.fromDict(r or {}, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def fetchGroupInfo(this, groupId):
        params, payload = this._buildFetchGroupInfo(groupId)
        data = this.PostSession(
            "https://tt-group-wpa.chat.zalo.me/api/group/getmg-v2",
            params=params,
            data=payload
        ).json()
        return this._parseFetchGroupInfo(data)

    async def fetchGroupInfoAsync(this, groupId):
        params, payload = this._buildFetchGroupInfo(groupId)
        data = await this.PostSessionAsync(
            "https://tt-group-wpa.chat.zalo.me/api/group/getmg-v2",
            params=params,
            data=payload
        )
        return this._parseFetchGroupInfo(data)