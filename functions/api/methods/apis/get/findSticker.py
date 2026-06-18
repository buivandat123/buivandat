from ....index import *

class SuggestStickerApi:
    def _buildSuggestSticker(this, keyword):
        return {
            "zpw_ver": 678,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "keyword": str(keyword or ""),
                "gif": 1,
                "guggy": 0,
                "imei": this._imei
            })
        }

    def _parseSuggestSticker(this, data):
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

    def findSticker(this, keyword):
        params = this._buildSuggestSticker(keyword)
        data = this.GetSession(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/suggest/stickers",
            params=params
        ).json()
        return this._parseSuggestSticker(data)

    async def findStickerAsync(this, keyword):
        params = this._buildSuggestSticker(keyword)
        resp = await this.GetSessionAsync(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/suggest/stickers",
            params=params
        )
        return this._parseSuggestSticker(await resp.json())