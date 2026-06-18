from functions.services.hook.anti_hook.classical_hook import *

def antiManager(this, message, data, userId, threadId, type):
    part = (message.text or "").strip().split()
    p = this.prefix
    c = this.rawCommand
    cm = f"{p}{c}"

    if len(part) < 2:
        helpText = f"""Anti for {this.groupHub(threadId)}, type a messageType to ignore this"""
        return this.sendMWarning(helpText, userId, threadId, type)

    key = part[1].lower()
    valid = {"all", "photo", "video", "gif", "file", "voice", "draw", "undo", "effect", "sticker", "recommended"}
    if key not in valid:
        return

    settings = ReadServices(this.uid)
    store = antiGetStore(settings)

    if key == "all":
        keys = {"photo", "video", "gif", "file", "voice", "draw", "undo", "effect", "sticker", "recommended"}
        enabledNow = all(antiIsEnabled(store, k, threadId) for k in keys)
        enabled = (not enabledNow) if len(part) < 3 else None
        if len(part) >= 3:
            action = part[2].lower()
            if action == "on":
                enabled = True
            elif action == "off":
                enabled = False
            else:
                enabled = not enabledNow
        antiSetAll(store, threadId, enabled)
        WriteService(this.uid, settings)
        status = "enabled" if enabled else "disabled"
        return this.sendMSuccess(f"Anti all is now {status}.", userId, threadId, type)

    enabled = antiIsEnabled(store, key, threadId)

    if len(part) < 3:
        enabled = not enabled
    else:
        action = part[2].lower()
        if action == "on":
            enabled = True
        elif action == "off":
            enabled = False
        else:
            enabled = not enabled

    antiSetEnabled(store, key, threadId, enabled)
    WriteService(this.uid, settings)

    status = "enabled" if enabled else "disabled"
    this.sendMSuccess(f"Anti {key} is now {status}.", userId, threadId, type)

dependencies = {
    "name": "anti",
    "permission": 3,
    "description": "Anti message by type",
    "cooldown": 3,
    "main": antiManager
}