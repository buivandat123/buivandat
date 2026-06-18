from ....index import *

class ChangeGroupAvatarApi:
    """
    Group API: Upload/Change group avatar by ID.

    Usage:
        r = api.changeGroupAvatar(filePath, groupId)
        r = await api.changeGroupAvatarAsync(filePath, groupId)
    """

    def _buildChangeGroupAvatar(this, filePath, groupId):
        if not os.path.exists(filePath):
            raise ZaloUserError(f"{filePath} not found")

        params = {
            "params": this._encode({
                "grid": str(groupId),
                "avatarSize": 120,
                "clientId": "g" + str(groupId) + utils.formatTime("%H:%M %d/%m/%Y"),
                "originWidth": 640,
                "originHeight": 640,
                "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None)
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        url = "https://tt-files-wpa.chat.zalo.me/api/group/upavatar"
        return url, params

    def _parseChangeGroupAvatar(this, data):
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

    def changeGroupAvatar(this, filePath, groupId):
        url, params = this._buildChangeGroupAvatar(filePath, groupId)
        with open(filePath, "rb") as f:
            files = { "fileContent": f }
            data = this.PostSession(url, params=params, files=files).json()
        return this._parseChangeGroupAvatar(data)

    async def changeGroupAvatarAsync(this, filePath, groupId):
        url, params = this._buildChangeGroupAvatar(filePath, groupId)

        if hasattr(this, "PostSessionAsync"):
            import aiohttp
            form = aiohttp.FormData()
            form.add_field(
                "fileContent",
                open(filePath, "rb"),
                filename=os.path.basename(filePath),
                content_type="application/octet-stream"
            )
            data = await this.PostSessionAsync(url, params=params, data=form)
            return this._parseChangeGroupAvatar(data)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, this.changeGroupAvatar, filePath, groupId)