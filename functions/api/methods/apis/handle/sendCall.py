from ....index import *

class SendCallApi:
    def _buildSendCall1(this, targetId, callId):
        url = f"https://voicecall-wpa.chat.zalo.me/api/voicecall/requestcall?zpw_ver=646&zpw_type={this.apiLogintype}"
        payloadParams = {
            "calleeId": targetId,
            "callId": callId,
            "codec": "[]\n",
            "typeRequest": 1,
            "imei": this._imei
        }
        return url, { "params": this._encode(payloadParams) }, { "params": this._encode(payloadParams) }

    def _buildSendCall2(this, targetId, callId, rtpAddress=None, rtcpAddress=None, codec=None):
        url = f"https://voicecall-wpa.chat.zalo.me/api/voicecall/request?zpw_ver=646&zpw_type={this.apiLogintype}"
        payloadParams = {
            "calleeId": targetId,
            "rtcpAddress": rtcpAddress or "171.244.25.88:4601",
            "rtpAddress": rtpAddress or "171.244.25.88:4601",
            "codec": codec or '[{"dynamicFptime":0,"frmPtime":20,"name":"opus/16000/1","payload":112}]\n',
            "session": callId,
            "callId": callId,
            "imei": this._imei,
            "subCommand": 3
        }
        return url, { "params": this._encode(payloadParams) }, { "params": this._encode(payloadParams) }

    def sendCall(this, target_id, callid_random, rtpAddress=None, rtcpAddress=None, codec=None):
        url1, params1, payload1 = this._buildSendCall1(target_id, callid_random)
        r1 = this.PostSession(url1, params=params1.get("params"), data=payload1)
        data1 = None
        try:
            data1 = r1.json()
        except:
            try:
                data1 = json.loads(r1.text or "{}")
            except:
                data1 = {}

        url2, params2, payload2 = this._buildSendCall2(target_id, callid_random, rtpAddress, rtcpAddress, codec)
        r2 = this.PostSession(url2, params=params2.get("params"), data=payload2)
        data2 = None
        try:
            data2 = r2.json()
        except:
            try:
                data2 = json.loads(r2.text or "{}")
            except:
                data2 = {}

        if (isinstance(data1, dict) and data1.get("error_code") not in (None, 0)) or (isinstance(data2, dict) and data2.get("error_code") not in (None, 0)):
            raise ZaloAPIException(f"Error when sending call: {data1 or r1.text} | {data2 or r2.text}")

        return { "requestcall": data1, "request": data2 }

    async def sendCallAsync(this, target_id, callid_random, rtpAddress=None, rtcpAddress=None, codec=None):
        url1, params1, payload1 = this._buildSendCall1(target_id, callid_random)
        r1 = await this.PostSessionAsync(url1, params=params1.get("params"), data=payload1)

        data1 = r1
        if not isinstance(r1, dict):
            try:
                data1 = json.loads(r1 or "{}")
            except:
                data1 = {}

        url2, params2, payload2 = this._buildSendCall2(target_id, callid_random, rtpAddress, rtcpAddress, codec)
        r2 = await this.PostSessionAsync(url2, params=params2.get("params"), data=payload2)

        data2 = r2
        if not isinstance(r2, dict):
            try:
                data2 = json.loads(r2 or "{}")
            except:
                data2 = {}

        if (isinstance(data1, dict) and data1.get("error_code") not in (None, 0)) or (isinstance(data2, dict) and data2.get("error_code") not in (None, 0)):
            raise ZaloAPIException(f"Error when sending call: {data1} | {data2}")

        return { "requestcall": data1, "request": data2 }