from ....index import *

class GetGroupMemberApi:
    def _buildGetGroupMember(this):
        return {"zpw_ver": 649, "zpw_type": this.apiLogintype}

    def _parseGetGroupMember(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("error_code") == 0 else r
            return r
        return None

    def _chunk(this, LST, SIZE):
        for i in range(0, len(LST), SIZE):
            yield LST[i:i + SIZE]

    def _fetchMembersOnce(this, MEMBER_LIST, PARAMS):
        payload = {"params": {"friend_pversion_map": MEMBER_LIST}}
        payload["params"] = this._encode(payload["params"])

        data = this.PostSession(
            "https://tt-profile-wpa.chat.zalo.me/api/social/group/members",
            params=PARAMS,
            data=payload
        ).json()

        r = this._parseGetGroupMember(data)
        if r is None:
            return None
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except:
                r = {"error_code": 1337, "error_message": r}
        if r is None:
            r = {"error_code": 1337, "error_message": "Data is None"}
        return r

    async def _fetchMembersOnceAsync(this, MEMBER_LIST, PARAMS):
        payload = {"params": {"friend_pversion_map": MEMBER_LIST}}
        payload["params"] = this._encode(payload["params"])

        resp = await this.PostSessionAsync(
            "https://tt-profile-wpa.chat.zalo.me/api/social/group/members",
            params=PARAMS,
            data=payload
        )
        data = await resp.json()

        r = this._parseGetGroupMember(data)
        if r is None:
            return None
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except:
                r = {"error_code": 1337, "error_message": r}
        if r is None:
            r = {"error_code": 1337, "error_message": "Data is None"}
        return r

    def getGroupMember(this, threadId):
        group = this.fetchGroupInfo(threadId).gridInfoMap[threadId]
        memlist = list(group.memVerList or [])
        if not memlist:
            raise ZaloAPIException("Không thể lấy thông tin thành viên")

        params = this._buildGetGroupMember()
        result = {"profiles": {}}

        for chunk in this._chunk(memlist, 500):
            r = this._fetchMembersOnce(chunk, params)
            if r and r.get("profiles"):
                result["profiles"].update(r["profiles"])

        if result["profiles"]:
            return Group.fromDict(result, None)
        raise ZaloAPIException("Không thể lấy thông tin thành viên")

    async def getGroupMemberAsync(this, threadId):
        group = this.fetchGroupInfo(threadId).gridInfoMap[threadId]
        memlist = list(group.memVerList or [])
        if not memlist:
            raise ZaloAPIException("Không thể lấy thông tin thành viên")

        params = this._buildGetGroupMember()
        result = {"profiles": {}}

        for chunk in this._chunk(memlist, 500):
            r = await this._fetchMembersOnceAsync(chunk, params)
            if r and r.get("profiles"):
                result["profiles"].update(r["profiles"])

        if result["profiles"]:
            return Group.fromDict(result, None)
        raise ZaloAPIException("Không thể lấy thông tin thành viên")