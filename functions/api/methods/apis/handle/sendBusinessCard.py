from ....index import *

class SendBusinessCardApi:
    def _buildSendBusinessCard(this, userId, qrCodeUrl, threadId, type, phone, ttl):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }

        msgInfo = {
            "contactUid": str(userId),
            "qrCodeUrl": str(qrCodeUrl)
        }
        if phone:
            msgInfo["phone"] = str(phone)

        payloadParams = {
            "ttl": ttl,
            "msgType": 6,
            "clientId": str(utils.now()),
            "msgInfo": json.dumps(msgInfo)
        }

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/forward"
            payloadParams["toId"] = str(threadId)
            payloadParams["imei"] = this._imei
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/forward"
            payloadParams["visibility"] = 0
            payloadParams["grid"] = str(threadId)
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = { "params": this._encode(payloadParams) }
        return url, params, payload, type

    def _parseSendBusinessCard(this, data, type):
        results = data.get("data") if data.get("error_code") == 0 else None
        if results:
            results = this._decode(results)
            results = results.get("data") if isinstance(results, dict) and results.get("data") else results

            if results is None:
                results = { "error_code": 1337, "error_message": "Data is None" }

            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    results = { "error_code": 1337, "error_message": results }

            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )

    def sendBusinessCard(this, userId, qrCodeUrl, threadId, type, phone=None, ttl=0):
        url, params, payload, tType = this._buildSendBusinessCard(
            userId, qrCodeUrl, threadId, type, phone, ttl
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendBusinessCard(data, tType)

    async def sendBusinessCardAsync(this, userId, qrCodeUrl, threadId, type, phone=None, ttl=0):
        url, params, payload, tType = this._buildSendBusinessCard(
            userId, qrCodeUrl, threadId, type, phone, ttl
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendBusinessCard(data, tType)