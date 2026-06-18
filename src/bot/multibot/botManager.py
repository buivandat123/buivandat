from functions.services.hook.core_hook.extra_multibot_core import *
from .args.createBot import *
from .args.createBotQR import *
from .args.deleteBot import *
from .args.manager.activeBot import *
from .args.manager.restartBot import *
from .args.manager.stopBot import *
from .args.manager.updateCredential import *
from .args.manager.changeOwner import *
from .args.manager.groupManager import *
from .args.serverInfo import *

def botManager(this, message, data, userId, threadId, type):
    try:
        parts = ((message.text or "").strip()).split()
        cmdb = f"{this.prefix}{this.rawCommand}"
        if len(parts) < 2:
            if this.mainBot:
                this.sendMWarning(
                    f"""
1. Create applications
{cmdb} create IMEI Session Cookies: Create with imei and cookies
{cmdb} create qr: Create with QR Code

2. Manager your applications:
{cmdb} list: All bots
{cmdb} info: Get Info
{cmdb} restart: Restart your BOT
{cmdb} stop: Stop your BOT
{cmdb} prefix: Set bot prefix
{cmdb} server: Get appServer
{cmdb} login: Set login type

3. Management for main
type {cmdb} manager.
    """,
                    userId, threadId, type
                )
            else:
                this.sendMWarning(
                    f"""Applications: {this.bot}
{cmdb} info: Get Info
{cmdb} restart: Restart your BOT
{cmdb} stop: Stop your BOT
{cmdb} prefix: Set bot prefix
{cmdb} server: Get appServer
{cmdb} login: Set login type
""",
                    userId, threadId, type
                )
            return

        cmd = parts[1].lower()
        isMain = IsMainBotUser(userId)
        hasMention = bool(GetMentionUid(this, data))

        if cmd == "manager":
            if not this.mainBot:
                this.sendMWarning("Only server can use {this.rawCommand}..!", userId, threadId, type)
                return
            manager = f"""{this.bot} Manager [Server]
    Set GROUP to get login status: {cmdb} group set
    Set send login status: {cmdb} group notify
    Delete userBot: {cmdb} delete [Target]
    Main can target a BOT with mentions or choose index of that BOT
"""
            this.sendMWarning(manager, userId, threadId, type)

        if cmd == "prefix":
            args = [x for x in parts[2:] if x != "|"]
            if this.mainBot:
                token = args[0] if (hasMention or (args and args[0].isdigit())) else None
                newPrefix = args[1] if token and len(args) >= 2 else (args[0] if args else None)
                if not newPrefix:
                    return this.sendMFailed("Set the prefix below the command!", userId, threadId, type)

                if token:
                    bot, fp, items = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
                    if not bot:
                        return
                    SaveBotField(fp, items, bot, "prefix", newPrefix)
                    return this.sendMSuccess(f"Updated prefix: {newPrefix}", userId, threadId, type)

                bot, fp, items = GetOwnBotByFilePath(this)
                if not bot:
                    bot, fp, items = GetOwnBot(this, data, userId, threadId, type)
                if not bot:
                    return this.sendMFailed("Cannot resolve this bot", userId, threadId, type)

                SaveBotField(fp, items, bot, "prefix", newPrefix)
                return this.sendMSuccess(f"Updated prefix: {newPrefix}", userId, threadId, type)

            bot, fp, items = GetOwnBotByFilePath(this)
            if not bot:
                bot, fp, items = GetOwnBot(this, data, userId, threadId, type)
            if not bot:
                return this.sendMFailed("Cannot resolve this bot", userId, threadId, type)

            newPrefix = args[0] if args else None
            if not newPrefix:
                return this.sendMFailed(f"Usage: {cmdb} prefix [Prefix]", userId, threadId, type)

            SaveBotField(fp, items, bot, "prefix", newPrefix)
            return this.sendMSuccess(f"Updated prefix: {newPrefix}", userId, threadId, type)

        token = parts[2] if len(parts) > 2 else None
        if not this.mainBot and cmd in ("create", "delete", "list", "group"):
            return this.sendMFailed("Permission denied, only server main.Bot%", userId, threadId, type)

        if cmd == "server":
            return this.sendMSuccess(this.appServer, userId, threadId, type)

        if cmd == "login":
            if len(parts) < 3:
                return this.sendMFailed("Set a login type: web or pc", userId, threadId, type)

            loginType = (parts[2] or "").lower()
            if loginType not in ("web", "pc"):
                return this.sendMFailed("Type support: web and pc", userId, threadId, type)

            loginValue = 30 if loginType == "web" else 24

            if this.mainBot:
                token = parts[3] if len(parts) > 3 else None
                if not token and not hasMention:
                    return this.sendMFailed("Target a bot to set login type", userId, threadId, type)

                bot, fp, items = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
                if not bot:
                    return
                SaveBotField(fp, items, bot, "login", loginValue)
                return this.sendMSuccess(f"Updated login type: {loginType.upper()} for {bot.get('username')}", userId, threadId, type)

            bot, fp, items = GetOwnBotByFilePath(this)
            if not bot:
                bot, fp, items = GetOwnBot(this, data, userId, threadId, type)
            if not bot:
                return this.sendMFailed("Cannot resolve this bot", userId, threadId, type)

            SaveBotField(fp, items, bot, "login", loginValue)
            this.sendMSuccess(f"Updated login type: {loginType.upper()}", userId, threadId, type)
            restartABot(bot)
            return

        if cmd == "info":
            if this.mainBot:
                if len(parts) >= 3 or hasMention:
                    bot, fp, _ = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
                    if not bot:
                        return
                    if IsMainBotTarget(fp, bot):
                        return this.sendMSuccess(TryBuildServerInfoText(this), userId, threadId, type)
                    return this.sendMSuccess(BuildBotInfoText(bot), userId, threadId, type)
                return this.sendMSuccess(TryBuildServerInfoText(this), userId, threadId, type)

            bot, fp, _ = GetOwnBotByFilePath(this)
            if not bot:
                bot, fp, _ = GetOwnBot(this, data, userId, threadId, type)
            if not bot:
                return this.sendMFailed("Cannot resolve this bot", userId, threadId, type)
            if IsMainBotTarget(fp, bot):
                return this.sendMSuccess(TryBuildServerInfoText(this), userId, threadId, type)
            return this.sendMSuccess(BuildBotInfoText(bot), userId, threadId, type)

        if not this.mainBot and cmd in ("restart", "stop"):
            bot, fp, items = GetOwnBotByFilePath(this)
            if not fp:
                return this.sendMFailed("Missing this filePath in basement", userId, threadId, type)
            if not bot:
                return this.sendMFailed("Cannot resolve this bot in login file", userId, threadId, type)

            if cmd == "stop":
                StopBot(this, bot, fp, items)
                return this.sendMSuccess("Your bot has been stopped", userId, threadId, type)

            RestartBot(this, bot, fp, items)
            return this.sendMSuccess("Restarted your bot..!", userId, threadId, type)

        if cmd == "create":
            if len(parts) > 2 and parts[2].lower() == "qr":
                return CreateBotQR(this, data, userId, threadId, type)
            message.text = " ".join(parts[2:])
            return CreateBot(this, message, data, userId, threadId, type)

        if cmd == "list":
            return ListBots(this, message, data, userId, threadId, type)

        if cmd == "group":
            if not isMain:
                return this.sendMFailed("Permission denied", userId, threadId, type)

            sub = parts[2].lower() if len(parts) > 2 else ""
            if sub == "set":
                link = setGroupLink(this, threadId)
                if not link:
                    return this.sendMFailed("Cannot get group link", userId, threadId, type)

                cfg = loadBotManager()
                dg = dataGroup(cfg)
                dg["groupSet"] = link
                botManagerSave(cfg)
                return this.sendMSuccess(f"Saved groupSet: {link}", userId, threadId, type)

            if sub == "notify":
                cfg = loadBotManager()
                dg = dataGroup(cfg)
                cur = dg.get("sendNotify")
                dg["sendNotify"] = False if cur is True else True
                botManagerSave(cfg)
                return this.sendMSuccess(f"sendNotify: {dg['sendNotify']}", userId, threadId, type)

            return this.sendMWarning("...", userId, threadId, type)

        if cmd == "update":
            if not isMain:
                return this.sendMFailed("Only mainBot can update the bot..!", userId, threadId, type)
            if len(parts) < 4 and not hasMention:
                return this.sendMFailed("Which bot will update?", userId, threadId, type)
            message.text = " ".join(parts[1:])
            return UpdateLoginCre(this, message, data, userId, threadId, type)

        if cmd == "changeowner":
            if not isMain:
                return this.sendMFailed("Permission denied", userId, threadId, type)
            return ChangeOwnerBot(this, message, data, userId, threadId, type)

        if cmd in ("restart", "stop") and not isMain:
            bot, fp, items = GetOwnBot(this, data, userId, threadId, type)
            if not bot:
                return
            if cmd == "stop":
                StopBot(this, bot, fp, items)
                return this.sendMSuccess("Your bot has been stopped", userId, threadId, type)
            RestartBot(this, bot, fp, items)
            return this.sendMSuccess("Restarted your bot..!", userId, threadId, type)

        if cmd == "start" and not isMain:
            if len(parts) != 2:
                return
            bot, fp, items = GetOwnBot(this, data, userId, threadId, type)
            if not bot or not bot.get("expiredTime"):
                return
            bot["status"] = True
            with open(fp, "w", encoding="utf-8") as f:
                f.write(json.dumps(items, ensure_ascii=False, indent=4))
            restartABot(bot)
            return this.sendMSuccess("Bot has been started", userId, threadId, type)

        if not isMain:
            return this.sendMFailed("Permission denied", userId, threadId, type)

        if cmd == "start":
            if len(parts) < 4 and not hasMention:
                return this.sendMFailed("Target a bot to start and set time", userId, threadId, type)
            timeExpr = parts[-1]
            bot, fp, items = GetBotByIndexOrMention(this, data, userId, threadId, type, token if len(parts) > 3 else None)
            if not bot:
                return
            ActiveBot(this, bot, fp, items, timeExpr)
            return this.sendMSuccess(f"Activated {bot.get('activedTime')} until {bot.get('expiredTime')} will expire..!", userId, threadId, type)

        if cmd == "restart":
            if len(parts) < 3 and not hasMention:
                return this.sendMFailed("Target a bot to restart", userId, threadId, type)
            bot, fp, items = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
            if not bot:
                return
            RestartBot(this, bot, fp, items)
            return this.sendMSuccess(f"Restarted {bot.get('username')}", userId, threadId, type)

        if cmd == "stop":
            if len(parts) < 3 and not hasMention:
                return this.sendMFailed("Target a bot to stop", userId, threadId, type)
            bot, fp, items = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
            if not bot:
                return
            StopBot(this, bot, fp, items)
            return this.sendMSuccess("Stopped", userId, threadId, type)

        if cmd == "delete":
            if len(parts) < 3 and not hasMention:
                return this.sendMFailed("Which one will bye the server?", userId, threadId, type)
            bot, fp, _ = GetBotByIndexOrMention(this, data, userId, threadId, type, token)
            if not bot:
                return
            if fp == mainLogin:
                return this.sendMFailed("Cannot delete main bot", userId, threadId, type)
            if not DeleteBot(this, bot, fp):
                return this.sendMFailed("Delete failed", userId, threadId, type)
            return this.sendMSuccess("Bot deleted from the system", userId, threadId, type)

        return

    except Exception as e:
        logger.errorMeta(f"Bot manager error: {e}")

dependencies = {
    "name": "myapp",
    "permission": 0,
    "description": "Create and manage bots",
    "cooldown": 3,
    "main": botManager
}