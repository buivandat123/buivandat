from functions.services.hook.bot_hook.approve_core import *

approveStart = False
def approveCommand(this, message, data, userId, threadId, type):
    parts = message.text.strip().split()
    settings = ReadServices(this.uid)
    approve = settings.setdefault("approveGroup", [])
    enabled = threadId in approve

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

    if enabled and threadId not in approve:
        approve.append(threadId)

    if not enabled and threadId in approve:
        approve.remove(threadId)
    WriteService(this.uid, settings)
    status = "enabled" if enabled else "disabled"
    this.sendMSuccess(
        f"Approve {this.groupHub(threadId)} is now {status}.",
        userId,
        threadId,
        type
    )



dependencies = {
    "name": "approve",
    "permission": 2,
    "description": "Auto Approve for GROUP",
    "cooldown": 5,
    "main": approveCommand
}