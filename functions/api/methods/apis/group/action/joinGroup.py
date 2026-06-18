from .....index import *

class JoinGroupApi:
    """
    Group API: Join group by invite link.

    Usage:
        r = api.joinGroup(inviteLink)
        r = await api.joinGroupAsync(inviteLink)
    """

    def _buildJoinGroup(this, url):
        params = {
            "zpw_ver": 648,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "link": str(url),
                "clientLang": "en"
            })
        }

        apiUrl = "https://tt-group-wpa.chat.zalo.me/api/group/link/join"
        return apiUrl, params, payload

    def _parseJoinGroup(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or "Unknown error"
            raise ZaloAPIException(f"Error #{errorCode}: {errorMessage}")

        raw = data.get("data")
        if not raw:
            raise ZaloAPIException("Error #1337: Data is None")

        try:
            return this._decode(raw)
        except Exception as e:
            raise ZaloAPIException(f"Decoding error: {str(e)}")

    def joinGroup(this, url):
        apiUrl, params, payload = this._buildJoinGroup(url)
        response = this.PostSession(apiUrl, params=params, data=payload)

        if not hasattr(response, "json"):
            raise ZaloAPIException(f"Unexpected response type: {type(response)}")

        data = response.json()
        return this._parseJoinGroup(data)

    async def joinGroupAsync(this, url):
        apiUrl, params, payload = this._buildJoinGroup(url)
        data = await this.PostSessionAsync(apiUrl, params=params, data=payload)
        return this._parseJoinGroup(data)
