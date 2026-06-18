from ....index import *

class FetchPhoneNumberApi:
    def _NormPhone(this, phoneNumber):
        s = "".join(ch for ch in str(phoneNumber or "").strip() if ch.isdigit() or ch == "+")
        if s.startswith("+"):
            s = s[1:]
        if s.startswith("84"):
            return s
        if s.startswith("0"):
            return "84" + s[1:]
        return "84" + s

    def _buildFetchPhoneNumber(this, phoneNumber, language):
        phone = this._NormPhone(phoneNumber)
        return {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "phone": phone,
                "avatar_size": 240,
                "language": language,
                "imei": this._imei,
                "reqSrc": 85
            })
        }

    def _parseFetchPhoneNumber(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("data") else r
            return User.fromDict(r or {}, None)
        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def fetchPhoneNumber(this, phoneNumber, language="vi"):
        params = this._buildFetchPhoneNumber(phoneNumber, language)
        data = this.GetSession(
            "https://tt-friend-wpa.chat.zalo.me/api/friend/profile/get",
            params=params
        ).json()
        return this._parseFetchPhoneNumber(data)

    async def fetchPhoneNumberAsync(this, phoneNumber, language="vi"):
        params = this._buildFetchPhoneNumber(phoneNumber, language)
        data = await this.GetSessionAsync(
            "https://tt-friend-wpa.chat.zalo.me/api/friend/profile/get",
            params=params
        )
        return this._parseFetchPhoneNumber(data)