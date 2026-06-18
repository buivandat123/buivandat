from ....index import *

class UpdateStickersPersonalApi:
    def _buildUpdateStickersPersonal(this, cateIds, version):
        if cateIds is None:
            cateIds = []
        if not isinstance(cateIds, (list, tuple)):
            cateIds = [cateIds]

        return {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "version": int(version or 0),
                "sticker_cates": [int(x) for x in cateIds if str(x).strip().isdigit()],
                "imei": this.imei
            })
        }

    def _parseUpdateStickersPersonal(this, data):
        if data.get("error_code") == 0 and data.get("data"):
            r = this._decode(data["data"])
            r = r.get("data") if isinstance(r, dict) and r.get("error_code") == 0 else r
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

    def updateStickersPersonal(this, cateIds, version):
        params = this._buildUpdateStickersPersonal(cateIds, version)
        data = this.GetSession(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/personalized/update",
            params=params
        ).json()
        return this._parseUpdateStickersPersonal(data)

    async def updateStickersPersonalAsync(this, cateIds, version):
        params = this._buildUpdateStickersPersonal(cateIds, version)
        resp = await this.GetSessionAsync(
            "https://tt-sticker-wpa.chat.zalo.me/api/message/sticker/personalized/update",
            params=params
        )
        return this._parseUpdateStickersPersonal(await resp.json())