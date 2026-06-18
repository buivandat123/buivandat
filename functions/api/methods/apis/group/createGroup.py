from ....index import *

class CreateGroupApi:
    """
    Group API: Create a new group.

    Usage:
        r = api.createGroup(
            name="Test Group",
            description="Hello",
            members=["uid1", "uid2"],
            createLink=1
        )

        r = await api.createGroupAsync(
            name="Test Group",
            description="Hello",
            members=["uid1", "uid2"],
            createLink=1
        )
    """

    def _buildCreateGroup(this, name, description, members, nameChanged, createLink):
        nameChanged = 1 if name else 0
        name = name or "Default Group Name"

        if members and isinstance(members, list):
            members = [str(x) for x in members]
        else:
            members = [str(members)] if members else []

        memberTypes = [-1] * len(members)

        payloadParams = {
            "clientId": utils.now(),
            "gname": name,
            "gdesc": description,
            "members": members,
            "memberTypes": memberTypes,
            "nameChanged": nameChanged,
            "createLink": createLink,
            "clientLang": "vi",
            "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None),
            "zsource": 601
        }

        params = {
            "params": this._encode(payloadParams),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-group-wpa.chat.zalo.me/api/group/create/v2"
        return url, params

    def _parseCreateGroup(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            return { "error_code": 1337, "error_message": "Data is None" }

        results = this._decode(results)
        results = results.get("data") if isinstance(results, dict) and results.get("data") else results

        if results is None:
            return { "error_code": 1337, "error_message": "Data is None" }

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                return { "error_code": 1337, "error_message": results }

        return results

    def createGroup(this, name=None, description=None, members=None, nameChanged=1, createLink=1):
        url, params = this._buildCreateGroup(name, description, members, nameChanged, createLink)
        data = this.GetSession(url, params=params).json()
        return this._parseCreateGroup(data)

    async def createGroupAsync(this, name=None, description=None, members=None, nameChanged=1, createLink=1):
        url, params = this._buildCreateGroup(name, description, members, nameChanged, createLink)
        data = await this.GetSessionAsync(url, params=params)
        return this._parseCreateGroup(data)