from dto.index import *

def listenCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").strip().split()
    settings = ReadServices(this.uid)
    allow = settings.setdefault("allowGroup", [])
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
    if type.name == "GROUP":
        group = f"{this.groupHub(tid)} {this.groupHub(tid).name}"
        res = (
            f"Bot {this.bot} is now listened in {group}"
            if is_on
            else f"Bot {this.bot} is now offline in {group}"
        )
    else:
        res = (
            f"Bot {this.bot} is now listened in private chat."
            if is_on
            else f"Bot {this.bot} is now offline in private chat."
        )

    this.sendMSuccess(res, userId, tid, type)

dependencies = {
    "name": "listen",
    "permission": 3,
    "cooldown": 2,
    "description": "Interact toggle",
    "main": listenCommand
}