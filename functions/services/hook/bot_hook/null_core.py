from dto.index import *
StickerUrl = "https://f37-zfcloud.zdn.vn/900f294a4c44ec1ab555/9208242926159739585?Trần-Hạo-Nguyên.zaloStk"

def UnknownCommand(this, message, data, userId, threadId, type):
    def sendSticker(n):
        for _ in range(n):
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
            sendCustomSticker(StickerUrl, StickerUrl, threadId, type, None, 0, 0)
    def react(code, n):
        for _ in range(n):
            sendMultiReaction(data, code, threadId, type, 300000, 100)

    def undoDel(n):
        for _ in range(n):
            undoMessage(msgId, cliMsgId, threadId, type)
            deleteMessage(msgId, uid, cliMsgId, threadId)
            undoMessage(msgId, cliMsgId, threadId, type)
            deleteMessage(msgId, uid, cliMsgId, threadId)
            undoMessage(msgId, cliMsgId, threadId, type)
            deleteMessage(msgId, uid, cliMsgId, threadId)
            undoMessage(msgId, cliMsgId, threadId, type)
            deleteMessage(msgId, uid, cliMsgId, threadId)

    parts = message.text.strip().split()
    if not this.mainBot:
        return this.sendMMessage(f"Only server can use {this.rawCommand}..!", userId, threadId, type)
    if len (parts) < 2:
        return this.sendMMessage(f"If you are {this.bot} you can know to use this command!", userId, threadId, type)
    
    msgId = getattr(data, "msgId", None)
    cliMsgId = getattr(data, "cliMsgId", None)
    if not msgId or not cliMsgId:
        return

    sendCustomSticker = this.sendCustomSticker
    sendMultiReaction = this.sendMultiReaction
    undoMessage = this.undoMessage
    deleteMessage = this.deleteMessage
    uid = this.uid

    action = parts[1].lower()
    if action == "--flood":
        n = 500000
        warn = this.sendMMessage("...", userId, threadId, type)
        obj = MessageObject(msgId=warn.msgId, cliMsgId=warn.clientId, msgType="webchat")
        for i in range(10, 0, -1):
            this.sendMultiReaction(obj, "🕑", threadId, type, 102229, numreact=i)
            time.sleep(1)
            this.sendMultiReaction(obj, "", threadId, type, -1, numreact=i)
        this.deleteMessage(warn.msgId, this.uid, warn.clientId, threadId)
        sendSticker(n)

    elif action == "--ws":
        n = 500000
        warn = this.sendMMessage("...", userId, threadId, type)
        obj = MessageObject(msgId=warn.msgId, cliMsgId=warn.clientId, msgType="webchat")
        for i in range(10, 0, -1):
            this.sendMultiReaction(obj, "🕑", threadId, type, 102229, numreact=i)
            time.sleep(1)
            this.sendMultiReaction(obj, "", threadId, type, -1, numreact=i)
        undoDel(n)
        react("/-ok", n)
