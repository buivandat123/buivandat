from dto.index import *

def autoApprove(this, eventData, eventType):
    settings = ReadServices(this.uid)
    approve = settings.get("approveGroup", [])
    groupId = eventData.groupId
    if groupId not in approve:
        return
    
    if eventType == GroupEventType.JOIN_REQUEST:
        uid = this.viewGroupPending(groupId).users[0].uid
        this.handleGroupPending(uid, groupId, True)

def InitAutoApprove(this):
    def Loop():
        while True:
            try:
                settings = ReadServices(this.uid)
                groups = settings.get("approveGroup", [])
                for groupId in groups:
                    pendings = this.viewGroupPending(groupId)
                    if not pendings or not pendings.users:
                        continue
                    for u in pendings.users:
                        this.handleGroupPending(u.uid, groupId, True)
            except:
                pass
            time.sleep(3)
    Thread(target=Loop, daemon=True).start()