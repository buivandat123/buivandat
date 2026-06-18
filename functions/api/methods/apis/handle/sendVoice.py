from ....index import *

class SendVoiceApi:
    """
    Message API: Send voice by url (forward).

    Usage:
        api.sendVoice(voiceUrl, threadId, type)
        await api.sendVoiceAsync(voiceUrl, threadId, type)
    """

    def _buildSendVoice(this, voiceUrl, threadId, type, fileSize, ttl):
        if not fileSize:
            try:
                r = this._state._session.get(voiceUrl)
                if r.status_code == 200:
                    fileSize = int(r.headers.get("Content-Length") or len(r.content))
                else:
                    fileSize = 0
            except Exception:
                fileSize = 0

        params = { "zpw_ver": 645, "zpw_type": this.apiLogintype, "nretry": 0 }

        payloadParams = {
            "ttl": ttl,
            "zsource": -1,
            "msgType": 3,
            "clientId": str(utils.now()),
            "msgInfo": json.dumps({
                "voiceUrl": str(voiceUrl),
                "m4aUrl": str(voiceUrl),
                "fileSize": int(fileSize or 0)
            })
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

    def _parseSendVoice(this, data, type):
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

    def sendVoice(this, voiceUrl, threadId, type, fileSize=None, ttl=0):
        url, params, payload, tType = this._buildSendVoice(
            voiceUrl, threadId, type, fileSize, ttl
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendVoice(data, tType)

    async def sendVoiceAsync(this, voiceUrl, threadId, type, fileSize=None, ttl=0):
        url, params, payload, tType = this._buildSendVoice(
            voiceUrl, threadId, type, fileSize, ttl
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendVoice(data, tType)