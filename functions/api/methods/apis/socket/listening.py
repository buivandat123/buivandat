from ....index import *
from ...core.AuthServices import *
import aiohttp
import inspect
import asyncio
import os
import signal
import json
from urllib.parse import urlencode, urlparse
from concurrent.futures import ThreadPoolExecutor


def _IsExecutorAlive(EXEC):
    if not EXEC:
        return False
    if getattr(EXEC, "_shutdown", False):
        return False
    return True


class ListeningApi(LoginAuth):
    def _buildListenWs(this):
        this.threadCondition.clear()
        params = {"zpw_ver": 647, "zpw_type": this.apiLogintype, "t": utils.now()}
        url = this._state._config["zpw_ws"][0] + "?" + urlencode(params)

        userAgent = this._state._headers.get("User-Agent") or utils.HEADERS["User-Agent"]
        rawCookies = this.GetSessionWsCookies()
        if not rawCookies:
            raise ZaloUserError("Unable to load cookies")

        wsHeadersList = [
            "Accept-Encoding: gzip, deflate, br, zstd",
            "Accept-Language: en-US,en;q=0.9",
            "Cache-Control: no-cache",
            "Connection: Upgrade",
            f"Host: {urlparse(url).netloc}",
            "Origin: https://chat.zalo.me",
            "Pragma: no-cache",
            "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits",
            "Sec-WebSocket-Version: 13",
            "Upgrade: websocket",
            f"User-Agent: {userAgent}",
            f"Cookie: {rawCookies}",
        ]

        wsHeadersDict = {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "Upgrade",
            "Host": urlparse(url).netloc,
            "Origin": "https://chat.zalo.me",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Sec-WebSocket-Version": "13",
            "Upgrade": "websocket",
            "User-Agent": userAgent,
            "Cookie": rawCookies,
        }

        return url, wsHeadersList, wsHeadersDict

    def _EnsurePool(this):
        ex = getattr(this, "bools", None)
        if _IsExecutorAlive(ex):
            return ex
        try:
            if ex:
                ex.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        this.bools = ThreadPoolExecutor(max_workers=8)
        return this.bools

    def _SubmitOrRun(this, FN, *A):
        try:
            this._EnsurePool().submit(FN, *A)
            return
        except RuntimeError:
            try:
                this.bools = None
                this._EnsurePool().submit(FN, *A)
                return
            except Exception:
                return FN(*A)

    def _dispatchMessage(this, msgObj, type):
        uidFrom = str(int(msgObj.uidFrom) or this.uid)
        if type == ThreadType.USER:
            toId = str(int(msgObj.uidFrom) or msgObj.idTo)
        else:
            toId = str(int(msgObj.idTo) or this.uid)

        if getattr(this, "thread", False):
            this._SubmitOrRun(this.messageListener, msgObj.msgId, uidFrom, msgObj.content, msgObj, toId, type)
        else:
            this.messageListener(msgObj.msgId, uidFrom, msgObj.content, msgObj, toId, type)

    def _dispatchEvent(this, eventData, eventType):
        if getattr(this, "thread", False):
            this._SubmitOrRun(this.eventListener, eventData, eventType)
        else:
            this.eventListener(eventData, eventType)

    def _dispatchUploadCallback(this, actType, content):
        d = content.get("data") or {}
        fileId = str(content.get("fileId"))
        fileUrl = d.get("url") if actType == "file_done" else (d.get("5") or d.get("6"))
        fileData = {"fileUrl": fileUrl, "fileId": content.get("fileId")}

        cb = this.uploadCallbacks.get(fileId) if hasattr(this, "uploadCallbacks") else None
        if cb:
            cb(fileData)
            del this.uploadCallbacks[fileId]
            return

        acb = this.uploadAsyncCallbacks.get(fileId) if hasattr(this, "uploadAsyncCallbacks") else None
        if not acb:
            return

        r = acb(fileData)
        if inspect.isawaitable(r):
            asyncio.run(r)
        del this.uploadAsyncCallbacks[fileId]

    async def _dispatchUploadCallbackAsync(this, actType, content):
        d = content.get("data") or {}
        fileId = str(content.get("fileId"))
        fileUrl = d.get("url") if actType == "file_done" else (d.get("5") or d.get("6"))
        fileData = {"fileUrl": fileUrl, "fileId": content.get("fileId")}

        cb = this.uploadCallbacks.get(fileId) if hasattr(this, "uploadCallbacks") else None
        if cb:
            cb(fileData)
            del this.uploadCallbacks[fileId]
            return

        acb = this.uploadAsyncCallbacks.get(fileId) if hasattr(this, "uploadAsyncCallbacks") else None
        if not acb:
            return

        r = acb(fileData)
        if inspect.isawaitable(r):
            await r
        del this.uploadAsyncCallbacks[fileId]

    def _handleDecodedPacket(this, version, cmd, subCmd, parsed, parsedData, wsCloseFn=None):
        if version == 1 and cmd == 3000 and subCmd == 0:
            logger.warning("Another connection is opened, closing this one")
            if wsCloseFn:
                wsCloseFn()
            return True

        if version == 1 and cmd == 501 and subCmd == 0:
            userMsgs = (parsedData.get("data") or {}).get("msgs") or []
            for message in userMsgs:
                msgObj = MessageObject.fromDict(message, None)
                this._dispatchMessage(msgObj, ThreadType.USER)
            return True

        if version == 1 and cmd == 521 and subCmd == 0:
            groupMsgs = (parsedData.get("data") or {}).get("groupMsgs") or []
            for message in groupMsgs:
                msgObj = MessageObject.fromDict(message, None)
                this._dispatchMessage(msgObj, ThreadType.GROUP)
            return True

        if version == 1 and cmd == 601 and subCmd == 0:
            controls = (parsedData.get("data") or {}).get("controls") or []
            for control in controls:
                content = control.get("content") or {}
                actType = content.get("act_type")

                if actType == "group":
                    act = content.get("act")
                    if act == "join_reject":
                        continue
                    raw = content.get("data")
                    groupEventData = json.loads(raw) if isinstance(raw, str) else raw
                    groupEventType = utils.getGroupEventType(act)
                    eventData = EventObject.fromDict(groupEventData)
                    this._dispatchEvent(eventData, groupEventType)
                    continue

                if actType in ("file_done", "voice_aac_success"):
                    this._dispatchUploadCallback(actType, content)
                    continue
            return True

        if cmd == 612:
            data612 = parsedData.get("data") or {}
            reacts = data612.get("reacts") or []
            reactGroups = data612.get("reactGroups") or []

            for react in reacts:
                react["content"] = json.loads(react["content"])
                msgObj = MessageObject.fromDict(react, None)
                this._dispatchMessage(msgObj, ThreadType.USER)

            for reactGroup in reactGroups:
                reactGroup["content"] = json.loads(reactGroup["content"])
                msgObj = MessageObject.fromDict(reactGroup, None)
                this._dispatchMessage(msgObj, ThreadType.GROUP)
            return True

        return False

    async def _handleDecodedPacketAsync(this, version, cmd, subCmd, parsed, parsedData, wsCloseFn=None):
        if version == 1 and cmd == 3000 and subCmd == 0:
            logger.warning("Another connection is opened, closing this one")
            if wsCloseFn:
                wsCloseFn()
            return True

        if version == 1 and cmd == 501 and subCmd == 0:
            userMsgs = (parsedData.get("data") or {}).get("msgs") or []
            for message in userMsgs:
                msgObj = MessageObject.fromDict(message, None)
                this._dispatchMessage(msgObj, ThreadType.USER)
            return True

        if version == 1 and cmd == 521 and subCmd == 0:
            groupMsgs = (parsedData.get("data") or {}).get("groupMsgs") or []
            for message in groupMsgs:
                msgObj = MessageObject.fromDict(message, None)
                this._dispatchMessage(msgObj, ThreadType.GROUP)
            return True

        if version == 1 and cmd == 601 and subCmd == 0:
            controls = (parsedData.get("data") or {}).get("controls") or []
            for control in controls:
                content = control.get("content") or {}
                actType = content.get("act_type")

                if actType == "group":
                    act = content.get("act")
                    if act == "join_reject":
                        continue
                    raw = content.get("data")
                    groupEventData = json.loads(raw) if isinstance(raw, str) else raw
                    groupEventType = utils.getGroupEventType(act)
                    eventData = EventObject.fromDict(groupEventData)
                    this._dispatchEvent(eventData, groupEventType)
                    continue

                if actType in ("file_done", "voice_aac_success"):
                    await this._dispatchUploadCallbackAsync(actType, content)
                    continue
            return True

        if cmd == 612:
            data612 = parsedData.get("data") or {}
            reacts = data612.get("reacts") or []
            reactGroups = data612.get("reactGroups") or []

            for react in reacts:
                react["content"] = json.loads(react["content"])
                msgObj = MessageObject.fromDict(react, None)
                this._dispatchMessage(msgObj, ThreadType.USER)

            for reactGroup in reactGroups:
                reactGroup["content"] = json.loads(reactGroup["content"])
                msgObj = MessageObject.fromDict(reactGroup, None)
                this._dispatchMessage(msgObj, ThreadType.GROUP)
            return True

        return False

    def _handleWsBinary(this, data, wsCloseFn=None):
        if not isinstance(data, (bytes, bytearray)) or len(data) < 5:
            return
        try:
            version, cmd, subCmd = utils.getHeader(data[:4])
            decodedData = data[4:].decode("utf-8", "ignore")
            if not decodedData or "eventId" in decodedData:
                return

            parsed = json.loads(decodedData)

            if version == 1 and cmd == 1 and subCmd == 1 and "key" in parsed:
                this.ws_key = parsed["key"]
                if hasattr(this, "ping_interval") and this.ping_interval:
                    this.ping_interval.cancel()
                this.PingSchedulerWS()
                return

            if not getattr(this, "ws_key", None):
                return logger.errorMeta("Unable to decrypt data because key not found")

            parsedData = utils.zws_decode(parsed, this.ws_key)
            this._handleDecodedPacket(version, cmd, subCmd, parsed, parsedData, wsCloseFn=wsCloseFn)

        except Exception as e:
            this.onErrorCallBack(e)

    async def _handleWsBinaryAsync(this, data, wsCloseFn=None):
        if not isinstance(data, (bytes, bytearray)) or len(data) < 5:
            return
        try:
            version, cmd, subCmd = utils.getHeader(data[:4])
            decodedData = data[4:].decode("utf-8", "ignore")
            if not decodedData or "eventId" in decodedData:
                return

            parsed = json.loads(decodedData)

            if version == 1 and cmd == 1 and subCmd == 1 and "key" in parsed:
                this.ws_key = parsed["key"]
                if hasattr(this, "ping_interval") and this.ping_interval:
                    this.ping_interval.cancel()
                this.PingSchedulerWS()
                return

            if not getattr(this, "ws_key", None):
                return logger.errorMeta("Unable to decrypt data because key not found")

            parsedData = utils.zws_decode(parsed, this.ws_key)
            await this._handleDecodedPacketAsync(version, cmd, subCmd, parsed, parsedData, wsCloseFn=wsCloseFn)

        except Exception as e:
            this.onErrorCallBack(e)

    def listening(this, thread=False, reconnect=5):
        url, wsHeadersList, _ = this._buildListenWs()

        def openListen(ws):
            this.listening = True
            this.onListening()

        def closeWebsocket(ws, status_code, msg):
            logger.info(f"WebSocket connection closed: {status_code} - {msg}")
            this.listening = False

        def pidKill(ws, error):
            if isinstance(error, KeyboardInterrupt):
                ws.close()
                logger.warning("Stop Listen Because KeyboardInterrupt Exception!")
                pid = os.getpid()
                os.kill(pid, signal.SIGTERM)
            this.onErrorCallBack(error)

        def wsMessage(ws, data):
            this._handleWsBinary(data, wsCloseFn=ws.close)

        this.ws = websocket.WebSocketApp(
            url,
            header=wsHeadersList,
            on_message=wsMessage,
            on_error=pidKill,
            on_close=closeWebsocket,
            on_open=openListen
        )

        this.thread = thread
        if not isinstance(reconnect, int):
            reconnect = 5
        this.ws.run_forever()

    async def listeningAsync(this, thread=False, reconnect=5):
        url, _, wsHeadersDict = this._buildListenWs()

        this.thread = thread
        if not isinstance(reconnect, int) or reconnect < 0:
            reconnect = 5

        tries = 0
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url, headers=wsHeadersDict, autoping=True, heartbeat=30) as ws:
                        this.ws = ws
                        this.listening = True
                        this.onListening()

                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.BINARY:
                                await this._handleWsBinaryAsync(msg.data, wsCloseFn=ws.close)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                raise ws.exception()
                            elif msg.type in (
                                aiohttp.WSMsgType.CLOSE,
                                aiohttp.WSMsgType.CLOSING,
                                aiohttp.WSMsgType.CLOSED,
                            ):
                                break

            except asyncio.CancelledError:
                this.listening = False
                raise
            except KeyboardInterrupt:
                this.listening = False
                logger.warning("Stop Listen Because KeyboardInterrupt Exception!")
                pid = os.getpid()
                os.kill(pid, signal.SIGTERM)
                return
            except Exception as e:
                this.listening = False
                this.onErrorCallBack(e)

            if reconnect == 0:
                return

            tries += 1
            if tries > reconnect:
                return

            await asyncio.sleep(1)

    def listen(this, thread=False, reconnect=5):
        this.thread = thread
        this._EnsurePool()
        this.listening(thread, reconnect)

    async def listenAsync(this, thread=False, reconnect=5):
        this.thread = thread
        this._EnsurePool()
        await this.listeningAsync(thread, reconnect)

    def onListening(this, phone=None):
        phone = this._state.phoneNumber
        this.temp_phoneNumber = phone
        bot = this.fetchAccountInfo().profile.displayName or ""
        logger.login(f"Listening for: {bot} - [{this.prefix}] - {this.uid} [{this.apiLogintype}] [{phone}]")