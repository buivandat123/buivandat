from ...core.AuthServices import *
from ....index import *

class stopListeningAPi:
    """
    Socket API: Stop listening and shutdown WebSocket.

    Usage:
        api.stopListening()
        await api.stopListeningAsync()
    """

    def stopListening(this):
        if hasattr(this, "ping_interval") and this.ping_interval:
            try:
                this.ping_interval.cancel()
            except:
                pass
            logger.info("WebSocket ping scheduler has been canceled.")

        if hasattr(this, "ws") and this.ws:
            try:
                this.ws.close()
                if hasattr(this, "bools") and hasattr(this.bools, "shutdown"):
                    this.bools.shutdown(wait=False)
            except:
                pass
            logger.info("WebSocket connection has been closed manually.")
        else:
            logger.warning("WebSocket is not running or already closed.")

        this.listening = False
        return True

    async def stopListeningAsync(this):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, this.stopListening)
        return True