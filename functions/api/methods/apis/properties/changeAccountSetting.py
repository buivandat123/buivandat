from ....index import *

class ChangeAccountSettingApi:
    """
    Account API: Change account profile information.

    Provides synchronous and asynchronous methods to update
    Zalo account profile such as name, date of birth and gender.

    Usage:
        api.changeAccountSetting("Nguyen Van A", "1999-01-01", 0)
        await api.changeAccountSettingAsync("Nguyen Van A", "1999-01-01", 0)
    """

    def _buildChangeAccountSetting(this, name, dob, gender, biz, language):
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}
        payload = {
            "params": this._encode({
                "profile": json.dumps({
                    "name": name,
                    "dob": dob,
                    "gender": int(gender)
                }),
                "biz": json.dumps(biz),
                "language": language
            })
        }
        return params, payload

    def _parseChangeAccountSetting(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if isinstance(r, dict) and r.get("data") else r
            if isinstance(r, str):
                try:
                    r = json.loads(r)
                except:
                    r = {"error_code": 1337, "error_message": r}
            return User.fromDict(r or {}, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def changeAccountSetting(this, name, dob, gender, biz=None, language="vi"):
        """
        Change account profile (sync).

        Args:
            name (str): New display name
            dob (str): Date of birth (YYYY-MM-DD)
            gender (int): 0 = Male, 1 = Female
            biz (dict): Business metadata (optional)
            language (str): Client language code

        Returns:
            User: Updated user information

        Raises:
            ZaloAPIException: Request failed
        """
        biz = biz or {}
        params, payload = this._buildChangeAccountSetting(
            name, dob, gender, biz, language
        )

        data = this.PostSession(
            "https://tt-profile-wpa.chat.zalo.me/api/social/profile/update",
            params=params,
            data=payload
        ).json()

        return this._parseChangeAccountSetting(data)

    async def changeAccountSettingAsync(this, name, dob, gender, biz=None, language="vi"):
        """
        Change account profile (async).

        Same behavior as changeAccountSetting but non-blocking.
        """
        biz = biz or {}
        params, payload = this._buildChangeAccountSetting(
            name, dob, gender, biz, language
        )

        data = await this.PostSessionAsync(
            "https://tt-profile-wpa.chat.zalo.me/api/social/profile/update",
            params=params,
            data=payload
        )

        return this._parseChangeAccountSetting(data)