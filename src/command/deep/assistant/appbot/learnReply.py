from dto.index import *

def learngetReply(this, message, data, userId, threadId, type):
    parts = (message.text or "").split()
    if len(parts)<2:
        this.sendMWarning("Learn what?", userId, threadId, type)
        return 
    
    key = parts[1]

    