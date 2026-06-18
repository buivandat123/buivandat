from ....index import *

class onSocketAPi:
    """
    Socket Event API: Handle socket callbacks.

    Usage:
        api.messageListener(mid, userId, message, data, threadId, type)
        await api.messageListenerAsync(mid, userId, message, data, threadId, type)

        api.eventListener(EventData, EventType)
        await api.eventListenerAsync(EventData, EventType)

        api.messageListenerDelivered(msg_ids, threadId, type, ts)
        await api.messageListenerDeliveredAsync(msg_ids, threadId, type, ts)

        api.onMarkedSeen(msg_ids, threadId, type, ts)
        await api.onMarkedSeenAsync(msg_ids, threadId, type, ts)

        api.onErrorCallBack(error, ts)
        await api.onErrorCallBackAsync(error, ts)
    """

    def messageListener(this, mid=None, userId=None, message=None, data=None, threadId=None, type=ThreadType.USER):
        logger.info("{} from {} in {}".format(message, threadId, type.name))

    async def messageListenerAsync(this, mid=None, userId=None, message=None, data=None, threadId=None, type=ThreadType.USER):
        this.messageListener(mid, userId, message, data, threadId, type)

    def eventListener(this, EventData, EventType):
        pass

    async def eventListenerAsync(this, EventData, EventType):
        this.eventListener(EventData, EventType)

    def messageListenerDelivered(this, msg_ids=None, threadId=None, type=ThreadType.USER, ts=None):
        logger.info(
            "Marked messages {} as delivered in [({}, {})] at {}.".format(
                msg_ids, threadId, type.name, int(ts / 1000) if ts else None
            )
        )

    async def messageListenerDeliveredAsync(this, msg_ids=None, threadId=None, type=ThreadType.USER, ts=None):
        this.messageListenerDelivered(msg_ids, threadId, type, ts)

    def onMarkedSeen(this, msg_ids=None, threadId=None, type=ThreadType.USER, ts=None):
        logger.info(
            "Marked messages {} as seen in [({}, {})] at {}.".format(
                msg_ids, threadId, type.name, int(ts / 1000) if ts else None
            )
        )

    async def onMarkedSeenAsync(this, msg_ids=None, threadId=None, type=ThreadType.USER, ts=None):
        this.onMarkedSeen(msg_ids, threadId, type, ts)

    def onErrorCallBack(this, error, ts=int(time.time())):
        if "login" in str(error):
            msg = "Imei Cookies Has Expired Or Null Error To Run!"
            logger.errorMeta(msg)
            print(f"[ERROR #{ts}] {msg}")
        else:
            logger.errorMeta(f"An error occurred at {ts}: {error}")
            print(traceback.format_exc())

    async def onErrorCallBackAsync(this, error, ts=int(time.time())):
        this.onErrorCallBack(error, ts)