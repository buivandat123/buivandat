from dto.index import *

def botMessage(this, message, data, userId, threadId, type):
    if message == "prefix":
        now = time.time()
        cooldown = 10

        key = f"prefix:{threadId}:{userId}"
        last = getattr(this, "cooldowns", {}).get(key, 0)
        remaining = int(cooldown - (now - last))

        if remaining > 0 or not isAdminHigh(this, userId):
            return this.sendCooldown(remaining, data, threadId, type)

        if not hasattr(this, "cooldowns"):
            this.cooldowns = {}
        this.cooldowns[key] = now

        return this.sendMSuccess(f"{this.bot} prefix is: {this.prefix}", userId, threadId, type)

    if message == this.prefix:
        now = time.time()
        cooldown = 10

        key = f"check:{threadId}:{userId}"
        last = getattr(this, "cooldowns", {}).get(key, 0)
        remaining = int(cooldown - (now - last))

        if remaining > 0 or not isAdminHigh(this, userId):
            return this.sendCooldown(remaining, data, threadId, type)

        if not hasattr(this, "cooldowns"):
            this.cooldowns = {}
        this.cooldowns[key] = now

        return this.sendMSuccess(f"Use {this.prefix}menu all to check all commands to use my bot", userId, threadId, type)