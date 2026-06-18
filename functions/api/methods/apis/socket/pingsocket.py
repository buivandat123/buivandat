from ....index import *

class pingSocket:
    """
    Socket API: WebSocket ping scheduler.

    Usage:
        api.PingSchedulerWS()
        await api.PingSchedulerWSAsync()
    """

    def _buildPingPayload(this):
        payload = {
            "version": 1,
            "cmd": 2,
            "subCmd": 1,
            "data": { "eventId": int(time.time() * 1000) }
        }

        encodedData = json.dumps(payload["data"]).encode()
        header = struct.pack("<BIB", payload["version"], payload["cmd"], payload["subCmd"])
        return header + encodedData

    def PingSchedulerWS(this):
        data = this._buildPingPayload()
        this.ws.send(data, websocket.ABNF.OPCODE_BINARY)

        this.ping_interval = threading.Timer(60, this.PingSchedulerWS)
        this.ping_interval.start()

    async def PingSchedulerWSAsync(this):
        data = this._buildPingPayload()

        if hasattr(this.ws, "send"):
            await asyncio.get_running_loop().run_in_executor(
                None,
                this.ws.send,
                data,
                websocket.ABNF.OPCODE_BINARY
            )

        await asyncio.sleep(60)
        await this.PingSchedulerWSAsync()