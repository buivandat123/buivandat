from .....index import *

class PinMessageApi:
    """
    Group API: Pin message in group by ID.

    Usage:
        r = api.pinMessage(pinMsg, groupId)
        r = await api.pinMessageAsync(pinMsg, groupId)
    """

    def _buildPinParamsPayload(this, pinMsg, groupId):
        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        p = {
            "grid": str(groupId),
            "type": 2,
            "color": -14540254,
            "emoji": "📌",
            "startTime": -1,
            "duration": -1,
            "repeat": 0,
            "src": -1,
            "imei": getattr(this, "_imei", None) or getattr(getattr(this, "_state", None), "clientUUID", None),
            "pinAct": 1
        }

        mt = getattr(pinMsg, "msgType", None)

        if mt in ("webchat", "chat.voice"):
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                **({ "title": pinMsg.content } if mt == "webchat" else {}),
                "msg_type": utils.getClientMessageType(mt)
            })

        elif mt in ("chat.photo", "chat.video.msg"):
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                "thumb": pinMsg.content.thumb,
                "title": pinMsg.content.description,
                "msg_type": utils.getClientMessageType(mt)
            })

        elif mt == "chat.sticker":
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                "extra": json.dumps({
                    "id": pinMsg.content.id,
                    "catId": pinMsg.content.catId,
                    "type": pinMsg.content.type
                }),
                "msg_type": utils.getClientMessageType(mt)
            })

        elif mt in ("chat.recommended", "chat.link"):
            extra = json.loads(pinMsg.content.params or "{}")
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                "href": pinMsg.content.href,
                "thumb": pinMsg.content.thumb or "",
                "title": pinMsg.content.title,
                "linkCaption": "https://chat.zalo.me/",
                "redirect_url": extra.get("redirect_url", ""),
                "streamUrl": extra.get("streamUrl", ""),
                "artist": extra.get("artist", ""),
                "stream_icon": extra.get("stream_icon", ""),
                "type": 2,
                "extra": json.dumps({
                    "action": pinMsg.content.action,
                    "params": json.dumps({
                        "mediaTitle": extra.get("mediaTitle", ""),
                        "artist": extra.get("artist", ""),
                        "src": extra.get("src", ""),
                        "stream_icon": extra.get("stream_icon", ""),
                        "streamUrl": extra.get("streamUrl", ""),
                        "type": 2
                    })
                }),
                "msg_type": utils.getClientMessageType(mt)
            })

        elif mt == "chat.location.new":
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                "msg_type": utils.getClientMessageType(mt),
                "title": pinMsg.content.title or pinMsg.content.description
            })

        elif mt == "share.file":
            extra = json.loads(pinMsg.content.params or "{}")
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                "title": pinMsg.content.title,
                "extra": json.dumps({
                    "fileSize": "7295",
                    "checksum": extra.get("checksum", ""),
                    "fileExt": extra.get("fileExt", ""),
                    "tWidth": extra.get("tWidth", 0),
                    "tHeight": extra.get("tHeight", 0),
                    "duration": extra.get("duration", 0),
                    "fType": extra.get("fType", 0),
                    "fdata": extra.get("fdata", "")
                }),
                "msg_type": utils.getClientMessageType(mt)
            })

        elif mt == "chat.gif":
            p["params"] = json.dumps({
                "client_msg_id": pinMsg.cliMsgId,
                "global_msg_id": pinMsg.msgId,
                "senderUid": str(int(pinMsg.uidFrom) or this.uid),
                "senderName": pinMsg.dName,
                "thumb": pinMsg.content.thumb,
                "msg_type": utils.getClientMessageType(mt)
            })

        payload = { "params": this._encode(p) }
        url = "https://groupboard-wpa.chat.zalo.me/api/board/topic/createv2"
        return url, params, payload

    def _parsePinMessage(this, data):
        if data.get("error_code") != 0:
            errorCode = data.get("error_code")
            errorMessage = data.get("error_message") or data.get("data")
            raise ZaloAPIException(f"Error #{errorCode} when sending requests: {errorMessage}")

        results = data.get("data")
        if not results:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        results = this._decode(results)
        results = results.get("data") if isinstance(results, dict) and results.get("data") else results

        if results is None:
            raise ZaloAPIException("Error #1337 when sending requests: Data is None")

        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                raise ZaloAPIException(f"Error #1337 when sending requests: {results}")

        return Group.fromDict(results, None)

    def pinMessage(this, pinMsg, groupId):
        url, params, payload = this._buildPinParamsPayload(pinMsg, groupId)
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parsePinMessage(data)

    async def pinMessageAsync(this, pinMsg, groupId):
        url, params, payload = this._buildPinParamsPayload(pinMsg, groupId)
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parsePinMessage(data)
