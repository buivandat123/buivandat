from dto.index import *

reactionStart = False

def ReactionsEvent(this, message, data, userId, type):
    if data.msgType != "chat.reaction":
        return

    ric = getattr(message, "rIcon", None)
    rmsg = getattr(message, "rMsg", None)
    msg = rmsg[0]
    cmsg = getattr(msg, "cMsgID", None)
    gmsg = getattr(msg, "gMsgID", None)

    if ric == "/-heart":
        setting = ReadServices(this.uid)
        mode = setting.get("undoMode", False)
        if mode:
            this.undoMessage(gmsg, cmsg, data.idTo, type)