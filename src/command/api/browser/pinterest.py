from functions.services.hook.media_hook.pinterest_hook import *

def handlePinterest(this, message, data, userId, threadId, type):
    try:
        parts = (message.text or "").split()
        keyword, limit = ParsePinterestArgs(parts)
        if not keyword:
            return this.sendMWarning("Type keyword to search images on Pinterest",userId,threadId,type)

        imageUrls = HandleOriginalPinterest(keyword, limit)
        if not imageUrls:
            return this.sendMWarning("Not found",userId,threadId,type)
        
        return this.sendMultiImage(imageUrls, threadId, type)
    except Exception as e:
        this.sendMFailed(e, userId, threadId, type)

dependencies = {
    "name": "pinterest",
    "description": "Search images on Pinterest",
    "main": handlePinterest
}