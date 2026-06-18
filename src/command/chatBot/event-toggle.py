from dto.index import *

def eventCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    settings = ReadServices(this.uid)
    allow = settings.setdefault("eventGroup", [])
    tid = threadId
    is_on = tid in allow
    action = parts[1].lower() if len(parts) > 1 else None

    if action == "on" and not is_on:
        allow.append(tid)
        is_on = True
    elif action == "off" and is_on:
        allow.remove(tid)
        is_on = False
    elif action is None:
        is_on = not is_on
        (allow.append if is_on else allow.remove)(tid)
    else:
        return

    WriteService(this.uid, settings)
    group = f"{this.groupHub(tid)} {this.groupHub(tid).name}"
    res = (
        f"Event {this.bot} is now enable in {group}"
        if is_on
        else f"Event is now disable in {group}"
    )
    this.sendMSuccess(res, userId, tid, type)

dependencies = {
    "name": "event",
    "permission": 3,
    "cooldown": 2,
    "description": "Event toggle",
    "main": eventCommand
}