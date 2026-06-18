from ....index import *

class SendReportApi:
    """
    Docstring for SendReportApi
    """
    def _buildSendReport(this, userId, type, reason, content):
        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype }

        payloadParams = {
            "idTo": str(userId),
            "objId": "person.profile"
        }

        content = content if (content and not reason) else (content if content and reason == 0 else "")
        if content:
            payloadParams["content"] = content

        payloadParams["reason"] = str(random.randint(1, 3) if not content else int(reason or 0))

        payload = { "params": this._encode(payloadParams) }
        url = "https://tt-profile-wpa.chat.zalo.me/api/report/abuse-v2"
        return url, params, payload, type

    def _parseSendReport(this, data, type):
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

    def sendReport(this, userId, type, reason=0, content=None):
        url, params, payload, tType = this._buildSendReport(userId, type, reason, content)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendReport(data, tType)

    async def sendReportAsync(this, userId, type, reason=0, content=None):
        url, params, payload, tType = this._buildSendReport(userId, type, reason, content)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendReport(data, tType)