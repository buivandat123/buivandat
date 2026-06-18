from ....index import *

class GetStickerDetailApi:
    def _buildGetStickerDetail(this, stickerId):
        return {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({"sid": int(stickerId or 0)})
        }

    def _parseGetStickerDetail(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if r.get("error_code") == 0 else r
            if r is None:
                return {"error_code": 1337, "error_message": "Data is None"}
            if isinstance(r, str):
                try:
                    r = json.loads(r)
                except:
                    return {"error_code": 1337, "error_message": r}
            return r

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def getStickerDetail(this, stickerId):
        params = this._buildGetStickerDetail(stickerId)
        data = this.GetSession(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/sticker_detail",
            params=params
        ).json()
        return this._parseGetStickerDetail(data)

    async def getStickerDetailAsync(this, stickerId):
        params = this._buildGetStickerDetail(stickerId)
        resp = await this.GetSessionAsync(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/sticker_detail",
            params=params
        )
        return this._parseGetStickerDetail(await resp.json())