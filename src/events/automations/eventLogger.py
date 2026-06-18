from src.queue.scheduler.autoApprove import autoApprove
from functions.services.hook.anti_hook.shield_hook import IsVerify
from src.events.joinGroup import isthisJoined
from src.events.automations.handle.event import *
from src.events.automations.handle.zaloEvent import *
eventStart = False
class EventZalo:
    def ZaloEvent(this, eventData, eventType):
        isthisJoined(this, eventData, eventType)
        IsVerify(this, eventData, eventType)
        autoApprove(this, eventData, eventType)
        ZaloEventHandle(this, eventData, eventType)