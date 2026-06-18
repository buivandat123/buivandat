from ....index import *

class ChangeAccountAvatarApi:
    """
    Account API: Change account avatar.

    Usage:
        api.changeAccountAvatar("avatar.png")
        await api.changeAccountAvatarAsync("avatar.png")
    """

    def _buildChangeAccountAvatar(this, filePath, width, height, language, size):
        if not os.path.exists(filePath):
            raise ZaloUserError(f"{filePath} not found")

        fileSize = size or os.stat(filePath).st_size
        files = [("fileContent", open(filePath, "rb"))]

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "avatarSize": 120,
                "clientId": f"{this.uid}{utils.formatTime('%H:%M %d/%m/%Y')}",
                "language": language,
                "metaData": json.dumps({
                    "origin": {"width": width, "height": height},
                    "processed": {
                        "width": width,
                        "height": height,
                        "size": fileSize
                    }
                })
            })
        }

        return params, files

    def _parseChangeAccountAvatar(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if isinstance(r, dict) and r.get("data") else r
            return User.fromDict(r or {}, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def changeAccountAvatar(this, filePath, width=500, height=500, language="vn", size=None):
        """
        Change account avatar (sync).
        """
        params, files = this._buildChangeAccountAvatar(
            filePath, width, height, language, size
        )

        data = this.PostSession(
            "https://tt-files-wpa.chat.zalo.me/api/profile/upavatar",
            params=params,
            files=files
        ).json()

        return this._parseChangeAccountAvatar(data)

    async def changeAccountAvatarAsync(this, filePath, width=500, height=500, language="vn", size=None):
        """
        Change account avatar (async).
        """
        params, files = this._buildChangeAccountAvatar(
            filePath, width, height, language, size
        )

        data = await this.PostSessionAsync(
            "https://tt-files-wpa.chat.zalo.me/api/profile/upavatar",
            params=params,
            files=files
        )

        return this._parseChangeAccountAvatar(data)