from functions.services.hook.anti_hook.antispam_hook import *

def antiSpamCommand(this, message, data, userId, threadId, type):
    parts = message.text.strip().split()

    settings = ReadServices(this.uid)
    antiSpam = settings.setdefault("antiSpam", [])
    enabled = threadId in antiSpam

    if len(parts) < 2:
        enabled = not enabled
    else:
        action = parts[1].lower()
        if action == "on":
            enabled = True
        elif action == "off":
            enabled = False
        else:
            return

    if enabled and threadId not in antiSpam:
        antiSpam.append(threadId)

    if not enabled and threadId in antiSpam:
        antiSpam.remove(threadId)

    WriteService(this.uid, settings)

    status = "enabled" if enabled else "disabled"
    try:
        this.sendMSuccess(f"Anti spamming is now {status}.", userId, threadId, type)
    except:
        pass

dependencies = {
    "name": "antispam",
    "permission": 2,
    "description": "Anti spam message",
    "cooldown": 5,
    "main": antiSpamCommand
}