from ....index import *

class ChangeGroupSettingApi:
    """
    Group API: Update group settings by ID.

    Usage:
        r = api.changeGroupSetting(
            groupId,
            defaultMode="default",
            blockName=1,
            signAdminMsg=1,
            addMemberOnly=0,
            setTopicOnly=1,
            enableMsgHistory=1,
            lockCreatePost=1,
            lockCreatePoll=1,
            joinAppr=1,
            lockSendMsg=0,
            lockViewMember=0,
            blocked_members=[]
        )

        r = await api.changeGroupSettingAsync(
            groupId,
            defaultMode="anti-raid",
            lockSendMsg=1
        )
    """

    def _getDefSetting(this, groupId, defaultMode):
        if defaultMode == "anti-raid":
            return {
                "blockName": 1,
                "signAdminMsg": 1,
                "addMemberOnly": 0,
                "setTopicOnly": 1,
                "enableMsgHistory": 1,
                "lockCreatePost": 1,
                "lockCreatePoll": 1,
                "joinAppr": 1,
                "bannFeature": 0,
                "dirtyMedia": 0,
                "banDuration": 0,
                "lockSendMsg": 0,
                "lockViewMember": 0,
            }
        gi = this.fetchGroupInfo(groupId).gridInfoMap
        return (gi.get(str(groupId)) or {}).get("setting") or {}

    def _buildChangeGroupSetting(this, groupId, defaultMode, kwargs):
        defSetting = this._getDefSetting(groupId, defaultMode)

        payloadParams = {
            "blockName": kwargs.get("blockName", defSetting.get("blockName", 1)),
            "signAdminMsg": kwargs.get("signAdminMsg", defSetting.get("signAdminMsg", 1)),
            "addMemberOnly": kwargs.get("addMemberOnly", defSetting.get("addMemberOnly", 0)),
            "setTopicOnly": kwargs.get("setTopicOnly", defSetting.get("setTopicOnly", 1)),
            "enableMsgHistory": kwargs.get("enableMsgHistory", defSetting.get("enableMsgHistory", 1)),
            "lockCreatePost": kwargs.get("lockCreatePost", defSetting.get("lockCreatePost", 1)),
            "lockCreatePoll": kwargs.get("lockCreatePoll", defSetting.get("lockCreatePoll", 1)),
            "joinAppr": kwargs.get("joinAppr", defSetting.get("joinAppr", 1)),
            "bannFeature": kwargs.get("bannFeature", defSetting.get("bannFeature", 0)),
            "dirtyMedia": kwargs.get("dirtyMedia", defSetting.get("dirtyMedia", 0)),
            "banDuration": kwargs.get("banDuration", defSetting.get("banDuration", 0)),
            "lockSendMsg": kwargs.get("lockSendMsg", defSetting.get("lockSendMsg", 0)),
            "lockViewMember": kwargs.get("lockViewMember", defSetting.get("lockViewMember", 0)),
            "blocked_members": kwargs.get("blocked_members", []),
            "grid": str(groupId),
            "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None)
        }

        params = {
            "params": this._encode(payloadParams),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/setting/update"
        return url, params

    def _parseChangeGroupSetting(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        results = this._decode(results)
        results = results.get("data") if isinstance(results, dict) and results.get("data") else results

        if results is None:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                raise ZaloAPIException(f"Error #1337 when sending requests: {results}")

        return Group.fromDict(results, None)

    def changeGroupSetting(this, groupId, defaultMode="default", **kwargs):
        url, params = this._buildChangeGroupSetting(groupId, defaultMode, kwargs)
        data = this.GetSession(url, params=params).json()
        return this._parseChangeGroupSetting(data)

    async def changeGroupSettingAsync(this, groupId, defaultMode="default", **kwargs):
        url, params = this._buildChangeGroupSetting(groupId, defaultMode, kwargs)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseChangeGroupSetting(data)