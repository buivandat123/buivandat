from .....index import *

class SetMuteApi:
    """
    Group API: Enable / Disable mute notifications for a group.

    Usage:
        api.setMute(groupId, True)    
        api.setMute(groupId, False)   

        await api.setMuteAsync(groupId, True)
        await api.setMuteAsync(groupId, False)
    """

    def _buildSetMute(this, groupId, mute):
        action = 1 if bool(mute) else 3

        params = {
            "zpw_ver": 664,
            "zpw_type": this.apiLogintype
        }

        payload = {
            "params": this._encode({
                "toid": str(groupId),
                "duration": -1,
                "action": action,
                "startTime": int(time.time()),
                "muteType": 2,
                "imei": getattr(this, "_imei", None)
                        or getattr(getattr(this, "_state", None), "clientUUID", None)
            })
        }

        url = "https://tt-profile-wpa.chat.zalo.me/api/social/profile/setmute"
        return url, params, payload

    def _parseSetMute(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data") or "Unknown error"
            raise ZaloAPIException(f"Error #{errorCode} - {errorMessage}")

        raw = data.get("data")
        if raw is None:
            raise ZaloAPIException("Error #1337: Data is None")

        if isinstance(raw, (dict, list)):
            return raw

        try:
            return this._decode(raw)
        except Exception as e:
            raise ZaloAPIException(f"Decoding error: {e}")

    def setMute(this, groupId, mute=True):
        url, params, payload = this._buildSetMute(groupId, mute)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSetMute(data)

    async def setMuteAsync(this, groupId, mute=True):
        url, params, payload = this._buildSetMute(groupId, mute)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSetMute(data)