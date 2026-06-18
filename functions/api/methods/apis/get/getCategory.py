from ....index import *

class getCategoryApi:
    def _buildFetchStickerById(this, catesId):
        return {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({"cid": catesId})
        }

    def _parseFetchStickerById(this, data):
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

    def getCategory(this, catesId):
        params = this._buildFetchStickerById(catesId)
        data = this.GetSession(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/category/sticker_detail",
            params=params
        ).json()
        return this._parseFetchStickerById(data)

    async def getCategoryAsync(this, catesId):
        params = this._buildFetchStickerById(catesId)
        resp = await this.GetSessionAsync(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/category/sticker_detail",
            params=params
        )
        return this._parseFetchStickerById(await resp.json())