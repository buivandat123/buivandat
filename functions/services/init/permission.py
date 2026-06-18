from functions.engine.data.data import *

def initAdmin(this):
    settings = ReadServices(this.uid)
    high_bot_admin = settings.get("highAdmin", [])
    if this.uid not in high_bot_admin:
        high_bot_admin.append(this.uid)
        settings["highAdmin"] = high_bot_admin
        WriteService(this.uid, settings)
    settings = ReadServices(this.uid)
    admin_bot = settings.get("adminBot", [])
    
    if this.uid not in admin_bot:
        admin_bot.append(this.uid)
        settings["adminBot"] = admin_bot
        WriteService(this.uid, settings)

    if this.getAdmin() not in high_bot_admin:
        high_bot_admin.append(this.getAdmin())
        settings["highAdmin"] = high_bot_admin
        WriteService(this.uid, settings)

def isAdminGroup(this, userId, threadId) -> bool:
    setting = ReadServices(this.uid)
    gradmin = setting.get("groupAdmin", [])
    if userId in gradmin:
        return True
    return False

def isAdminHigh(this, userId) -> bool:
    setting = ReadServices(this.uid)
    highadmin = setting.get("highAdmin", [])
    if userId in highadmin:
        return True
    return False

def isAdminBot(this, userId) -> bool:
    setting = ReadServices(this.uid)
    adminbot = setting.get("adminBot", [])
    if userId in adminbot:
        return True
    return False

def isWhitelisted(this, userId, threadId) -> bool:
    settings = ReadServices(this.uid)
    whitelist = settings.get("whitelist", {})
    group_whitelist = whitelist.get(threadId, [])
    return userId in group_whitelist

def AdminAll(this, threadId, userId):
    return (
        isAdminHigh(this, userId)
        or isAdminBot(this, userId)
        or isAdminGroup(this, userId, threadId)
    )


def isModerator(this, uid, threadId):
    grInfo = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {}) or {}
    adminIds = set(grInfo.get("adminIds", []) or [])
    creatorId = grInfo.get("creatorId")
    if not uid:
        return False
    if creatorId and str(uid) == str(creatorId):
        return True
    return str(uid) in {str(x) for x in adminIds}

def skip(this, userId, threadId) -> bool:
    return AdminAll(this, threadId, userId) or isWhitelisted(this, userId, threadId)