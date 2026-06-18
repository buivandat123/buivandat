from src.bot.system.evalExecutor import PrettyJson
from dto.index import *

settingLabels = {
    "blockName": ("bật", "tắt", "chặn đổi tên nhóm"),
    "signAdminMsg": ("bật", "tắt", "đánh dấu tin nhắn admin"),
    "addMemberOnly": ("bật", "tắt", "chế độ chỉ admin được thêm thành viên"),
    "setTopicOnly": ("bật", "tắt", "chế độ chỉ admin được đổi chủ đề"),
    "enableMsgHistory": ("bật", "tắt", "lịch sử trò chuyện"),
    "joinAppr": ("bật", "tắt", "duyệt thành viên"),
    "lockCreatePost": ("khóa", "mở", "đăng bài"),
    "lockCreatePoll": ("chặn", "mở", "tạo bình chọn"),
    "lockSendMsg": ("khóa", "mở", "trò chuyện"),
    "lockViewMember": ("ẩn", "mở", "danh sách thành viên")
}

def eventStatus(this):
    settings = ReadServices(this.uid) or {}
    return settings.get("eventGroup", [])

def getField(data, key, default=None):
    if isinstance(data, dict):
        return data.get(key, default)
    return getattr(data, key, default)

def getMembers(eventData):
    members = getField(eventData, "updateMembers", [])
    return members if isinstance(members, list) else []

def getSetting(eventData):
    setting = getField(eventData, "groupSetting", {})
    return setting if isinstance(setting, dict) else {}

def getMemberInfo(member):
    if not isinstance(member, dict):
        return "", "", ""
    return (
        str(member.get("id") or ""),
        str(member.get("dName") or ""),
        str(member.get("avatar") or "")
    )

def getGroupSettingStore(this):
    services = ReadServices(this.uid) or {}
    store = services.get("groupSettingState", {})
    return store if isinstance(store, dict) else {}

def saveGroupSettingStore(this, store):
    services = ReadServices(this.uid) or {}
    services["groupSettingState"] = store
    WriteService(this.uid, services)

def findChangedSetting(oldSetting, newSetting):
    for key in settingLabels:
        oldValue = int(oldSetting.get(key, 0) or 0)
        newValue = int(newSetting.get(key, 0) or 0)
        if oldValue != newValue:
            return key, newValue
    return None, None

def makeSettingMessage(actorName, hub, key, value):
    onText, offText, label = settingLabels[key]
    action = onText if int(value or 0) else offText
    return f"{actorName} vừa {action} {label} ở {hub}"

def ZaloEventHandle(this, eventData, eventType):
    if not (eventData.groupId in eventStatus(this)):
        return

    logger.debug(f"{PrettyJson(eventData)}\n{eventType}")

    groupId = str(getField(eventData, "groupId", "") or "")
    groupName = str(getField(eventData, "groupName", "") or "")
    sourceId = str(getField(eventData, "sourceId", "") or "")
    members = getMembers(eventData)
    setting = getSetting(eventData)
    event = GroupEventType
    hub = this.groupHub(groupId)
    actorName = this.userName(sourceId)

    uid = ""
    name = ""
    avatar = ""
    if members:
        uid, name, avatar = getMemberInfo(members[0])

    def debugSend(messageText="", mentionUid=None):
        return this.sendMCustom(
            "EVENT",
            "y",
            messageText,
            mentionUid,
            groupId,
            ThreadType.GROUP
        )

    if eventType == event.JOIN:
        if sourceId and sourceId != uid:
            return debugSend(
                f"{name} vừa tham gia {hub} {groupName} được mời bởi {actorName}",
                uid
            )
        return debugSend(f"{name} vừa tham gia {hub} {groupName}", uid)

    if eventType == event.LEAVE:
        return debugSend(f"{name} vừa rời khỏi {hub} {groupName}")

    if eventType == event.REMOVE_MEMBER:
        return debugSend(f"{name} vừa bị đá khỏi {hub} {groupName} bởi {actorName}")

    if eventType == event.REMOVE_ADMIN:
        return debugSend(f"{name} vừa bị hạ quyền quản trị ở {hub} bởi {actorName}", uid)

    if eventType == event.ADD_ADMIN:
        return debugSend(f"{name} vừa được nâng quyền quản trị ở {hub} bởi {actorName}", uid)

    if eventType == event.UPDATE_SETTING:
        if not setting:
            return

        store = getGroupSettingStore(this)
        oldSetting = store.get(groupId, {})
        oldSetting = oldSetting if isinstance(oldSetting, dict) else {}

        if not oldSetting:
            store[groupId] = dict(setting)
            saveGroupSettingStore(this, store)
            return

        changedKey, changedValue = findChangedSetting(oldSetting, setting)

        store[groupId] = dict(setting)
        saveGroupSettingStore(this, store)

        if not changedKey:
            return

        return debugSend(makeSettingMessage(actorName, hub, changedKey, changedValue))