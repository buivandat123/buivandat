
from src.events.automations.eventUser import botMessage
from src.events.automations.eventReaction import ReactionsEvent
from src.queue.scheduler.services import handleListenAnti
from src.events.automations.handle.message import *
eventListen = False

class MessageZalo:
    def MessageHandler(this, mid, userId, message, data, threadId, type):
        this.skipMessage(data)
        allow = getAllowed(this)
        this.getRecommended(data)
        this.senderInfo[this.userName(userId)] = message

        forward = False
        try:
            if getattr(data, "reference", None) and data.reference.get("data"):
                forward = bool(json.loads(data.reference["data"]).get("fwLvl"))
        except:
            forward = False

        handleListenAnti(this, message, data, userId, threadId, type)
        if not (threadId in allow or AdminAll(this, threadId, userId)):
            return

        logMessage(this, logger, chat_type=type.name, message=message, data=data, forward=forward)
        ReactionsEvent(this, message, data, userId, type)
        botMessage(this, message, data, userId, threadId, type)

        this.LoadCommands(message, data, userId, threadId, type)
        this.listenReply(message, data, userId, threadId, type)