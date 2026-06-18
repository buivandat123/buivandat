from functions.services.hook.anti_hook.antibot_hook import *

def antiBotCommand(this, message, data, userId, threadId, type):
    parts = (message.text or "").split()
    s = ReadServices(this.uid)
    a = s.setdefault("antiBot", [])
    cur = threadId in a

    arg = (parts[1].lower() if len(parts) > 1 else "")
    e = (not cur) if not arg else (arg == "on") if arg in ("on", "off") else None
    if e is None:
        return

    (a.append(threadId) if e and not cur else a.remove(threadId) if (not e) and cur else None)
    WriteService(this.uid, s)
    this.sendMSuccess(f"Anti bot is now {'enabled, will block all bots' if e else 'disabled'}.", userId, threadId, type)

dependencies = {
    "name": "antibot",
    "permission": 2,
    "description": "Anti chat bot",
    "cooldown": 5,
    "main": antiBotCommand
}