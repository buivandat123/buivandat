from functions.services.hook.core_hook.extra_multibot_core import *

def UpdateExistingBotLogin(uidFrom, imei, sessionCookies):
    dataConfig = jsonLoader(mainLogin) or {}
    dataBot = dataConfig.get("dataBot", {})
    if not isinstance(dataBot, dict):
        return None, None, None

    loginFile = dataBot.get(str(uidFrom))
    if not loginFile:
        return None, None, None

    loginPath = os.path.join("assets", "config", "multibot", loginFile)
    items = jsonLoader(loginPath)
    if not isinstance(items, list) or not items:
        return None, None, None

    bot = items[0] if isinstance(items[0], dict) else None
    if not bot:
        return None, None, None

    bot["imei"] = imei
    bot["sessionCookies"] = sessionCookies

    with open(loginPath, "w", encoding="utf-8") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=4))

    return bot, loginPath, items

def CreateBotQR(this, data, userId, threadId, type):
    uidFrom = GetUidFrom(data)
    u = uidFrom
    tu = ThreadType.USER
    waitMessage = this.sendMCustom("WAITING", "y", "Creating QR code for login...", userId, threadId, type)

    sessions = verifyClient(SessionHeader())
    code, sessions = GenerateLoginQr(sessions)

    qrImagePath = "assets/cache/qr_code.png"
    up = this.uploadImage(qrImagePath, threadId, type)
    qrHdUrl = up.get("hdUrl") if up else None
    this.deleteMessage(waitMessage.msgId, this.uid, waitMessage.clientId, threadId)
    this.sendMSuccess("Sent Login QRCodes for u, check direct message..!", uidFrom, threadId, type)
    notifyQr = this.sendMCustom("WAITING", "y", "Scan this QRCodes by another devices to login..", userId, threadId, type)
    msg = this.sendImage(
        imageUrl=qrHdUrl,
        message=Message(text=None),
        threadId=uidFrom,
        type=ThreadType.USER
    )

    qrMsgId = getattr(msg, "msgId", None)
    qrCliId = getattr(msg, "clientId", None)

    def ProcessQRAuth():
        def DelQr():
            this.undoMessage(notifyQr.msgId, notifyQr.clientId, u, tu)
            this.undoMessage(qrMsgId, qrCliId, u, tu)
            if os.path.exists(qrImagePath):
                os.remove(qrImagePath)

        try:
            scanResult = waiting_scan(code, sessions)
            if not scanResult:
                DelQr()
                this.sendMFailed("QR code scan timeout", userId, u, tu)
                return

            qrData = waiting_confirm(code, sessions)
            DelQr()
            if not qrData:
                this.sendMFailed("Authentication failed", userId, u, tu)
                return

            imei = qrData.get("imei")
            sessionCookies = qrData.get("cookie", {})

            bot, _, _ = UpdateExistingBotLogin(uidFrom, imei, sessionCookies)
            if bot:
                this.sendMSuccess(f"Updated IMEI & Cookies for {bot.get('username')}", userId, u, tu)
                return

            dataConfig = jsonLoader(mainLogin) or {}
            dataBot = dataConfig.get("dataBot", {})
            if not isinstance(dataBot, dict):
                dataBot = {}

            botIntId = str(userId)
            username = f"{this.userName(uidFrom)}-{len(dataConfig.get('data', []))}"
            prefix = qrData.get("prefix", "?")
            botAccount = SlugName(username)
            botPassword = str(this.randomInt())

            newBot = {
                "username": username,
                "login": 24,
                "botIntId": botIntId,
                "imei": imei,
                "prefix": prefix,
                "sessionCookies": sessionCookies,
                "clientBotId": str(uidFrom),
                "mainBot": False,
                "status": False,
                "isActived": False,
                "botAccount": botAccount,
                "botPassword": botPassword
            }

            os.makedirs(os.path.join("assets", "config", "multibot"), exist_ok=True)

            indexFile = 1
            while os.path.exists(os.path.join("assets", "config", "multibot", f"{indexFile}-login.json")):
                indexFile += 1

            loginFile = f"{indexFile}-login.json"
            loginPath = os.path.join("assets", "config", "multibot", loginFile)

            items = [newBot, {"userClientId": str(uidFrom)}]
            with open(loginPath, "w", encoding="utf-8") as f:
                f.write(json.dumps(items, ensure_ascii=False, indent=4))

            dataBot[str(uidFrom)] = loginFile
            dataConfig["dataBot"] = dataBot
            saveJson(mainLogin, dataConfig)

            this.sendMCustom(
                "WAITING APPROVE", "y",
                f"""
Bot: {this.userName(uidFrom)}
Prefix: {prefix}

Server: {this.appServer}
Account: {botAccount}
Password: {botPassword}

Wait to Master Bot approve your BOT
""",
                userId,
                userId,
                ThreadType.USER
            )

        except Exception as e:
            try:
                DelQr()
            except Exception:
                pass
            try:
                this.sendMFailed(f"CreateBotQR error: {e}", userId, u, tu)
            except Exception:
                pass

    threading.Thread(target=ProcessQRAuth, daemon=True).start()