from ..util.pack import *
from ..util import utils
from ..app import State

class UtilServices:
    def GetSession(this, *args, **kwargs):
        return this._state.GetSession(*args, **kwargs)

    def PostSession(this, *args, **kwargs):
        return this._state.PostSession(*args, **kwargs)

    async def GetSessionAsync(this, *args, **kwargs):
        return await this._state.GetSessionAsync(*args, **kwargs)

    async def PostSessionAsync(this, *args, **kwargs):
        return await this._state.PostSessionAsync(*args, **kwargs)

    def _encode(this, params):
        return utils.zalo_encode(params, this._state._config.get("secretkey"))

    def _decode(this, params):
        return utils.zalo_decode(params, this._state._config.get("secretkey"))

    def _decodeZwsk(this, params):
        return utils.zws_decode(json.loads(params), this.ws_key)

    def _GetImei(this):
        return getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None)

    def _ParseData(this, data):
        if data.get("error_code") != 0:
            return None
        results = data.get("data")
        if not results:
            return None
        results = this._decode(results) if isinstance(results, str) else results
        if isinstance(results, dict) and results.get("data") is not None:
            return results.get("data")
        return results

    def makeCall(this, uid):
        callId = int(time.time())
        params = {
            "params": this._encode({
                "calleeId": str(uid),
                "callId": callId,
                "codec": "[]\n",
                "typeRequest": 1,
                "imei": this._GetImei()
            }),
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype
        }
        data = this.GetSession("https://voicecall-wpa.chat.zalo.me/api/voicecall/requestcall", params=params).json()
        parsed = this._ParseData(data)
        if not parsed:
            return None
        parsed["callId"] = callId
        return parsed

    async def makeCallAsync(this, uid):
        callId = int(time.time())
        params = {
            "params": this._encode({
                "calleeId": str(uid),
                "callId": callId,
                "codec": "[]\n",
                "typeRequest": 1,
                "imei": this._GetImei()
            }),
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype
        }
        data = await this.GetSessionAsync("https://voicecall-wpa.chat.zalo.me/api/voicecall/requestcall", params=params)
        parsed = this._ParseData(data)
        if not parsed:
            return None
        parsed["callId"] = callId
        return parsed

    def makeCallRequest(this, uid, data_call):
        sampleRate = data_call["zrtc_config"]["audioSampleRate"]
        channels = data_call["zrtc_config"]["audioChannel"]
        codec = json.dumps([{
            "dynamicFptime": 0,
            "frmPtime": 20,
            "name": f"opus/{sampleRate}/{channels}",
            "payload": 112
        }])

        params = {
            "params": this._encode({
                "calleeId": str(uid),
                "rtcpAddress": data_call["rtpIP"],
                "rtpAddress": data_call["rtpIP"],
                "codec": codec,
                "session": data_call["sessId"],
                "callId": data_call["callId"],
                "imei": this._GetImei(),
                "extendData": json.dumps({
                    "supportCallBusy": data_call["settings"]["supportCallBusy"],
                    "tpType": 0,
                    "video": json.dumps({"codec": [{"name": "h264", "payload": 97}]})
                }),
                "subCommand": 3
            }),
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype
        }
        data = this.GetSession("https://voicecall-wpa.chat.zalo.me/api/voicecall/request", params=params).json()
        return this._ParseData(data)

    async def makeCallRequestAsync(this, uid, data_call):
        sampleRate = data_call["zrtc_config"]["audioSampleRate"]
        channels = data_call["zrtc_config"]["audioChannel"]
        codec = json.dumps([{
            "dynamicFptime": 0,
            "frmPtime": 20,
            "name": f"opus/{sampleRate}/{channels}",
            "payload": 112
        }])

        params = {
            "params": this._encode({
                "calleeId": str(uid),
                "rtcpAddress": data_call["rtpIP"],
                "rtpAddress": data_call["rtpIP"],
                "codec": codec,
                "session": data_call["sessId"],
                "callId": data_call["callId"],
                "imei": this._GetImei(),
                "extendData": json.dumps({
                    "supportCallBusy": data_call["settings"]["supportCallBusy"],
                    "tpType": 0,
                    "video": json.dumps({"codec": [{"name": "h264", "payload": 97}]})
                }),
                "subCommand": 3
            }),
            "zpw_ver": 650,
            "zpw_type": this.apiLogintype
        }
        data = await this.GetSessionAsync("https://voicecall-wpa.chat.zalo.me/api/voicecall/request", params=params)
        return this._ParseData(data)

    def randomInt(this):
        return "".join(str(random.randint(0, 9)) for _ in range(9))