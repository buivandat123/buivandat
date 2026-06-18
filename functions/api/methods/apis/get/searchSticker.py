from ....index import *

class SearchStickerApi:
    def _buildSearchSticker(this, KEYWORD, LIMIT=50):
        return {
            "zpw_ver": 678,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "keyword": str(KEYWORD or ""),
                "limit": int(LIMIT or 50),
                "srcType": 0,
                "imei": this._imei
            })
        }

    def _parseSearchSticker(this, data):
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

    def searchSticker(this, KEYWORD, LIMIT=50):
        params = this._buildSearchSticker(KEYWORD, LIMIT)
        data = this.GetSession(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/search",
            params=params
        ).json()
        return this._parseSearchSticker(data)

    async def searchStickerAsync(this, KEYWORD, LIMIT=50):
        params = this._buildSearchSticker(KEYWORD, LIMIT)
        resp = await this.GetSessionAsync(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/search",
            params=params
        )
        return this._parseSearchSticker(await resp.json())