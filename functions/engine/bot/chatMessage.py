from dto.index import *

ghostDelay = 60

class AntiFunctions:
    def skipMessage(this, data):
        if not hasattr(this, "clicc") or not isinstance(this.clicc, set):
            this.clicc = set()
        cliId = getattr(data, "cliMsgId", None)
        if cliId is None or cliId in this.clicc:
            return
        this.clicc.add(cliId)


class GhostFunctions:
    def isGhostStatus(this):
        s = ReadServices(this.uid)
        return bool((s or {}).get("ghostStatus", False))

    def initDeleteMessage(this):
        if getattr(this, "ghostLoop", False):
            return
        this.ghostLoop = True

        if not hasattr(this, "ghostMessage") or not isinstance(this.ghostMessage, dict):
            this.ghostMessage = {}

        def loop():
            while True:
                time.sleep(ghostDelay)
                if not this.isGhostStatus():
                    continue

                now = time.time()
                for k, v in list(this.ghostMessage.items()):
                    if not isinstance(v, dict):
                        this.ghostMessage.pop(k, None)
                        continue

                    try:
                        ts = float(v.get("ts") or 0)
                    except Exception:
                        ts = 0

                    if ts <= 0 or (now - ts) < ghostDelay:
                        continue

                    msgId = v.get("msgId")
                    clientId = v.get("clientId")
                    threadId = v.get("threadId")

                    try:
                        if msgId and clientId and threadId:
                            this.deleteMessage(msgId, this.uid, clientId, threadId)
                    finally:
                        this.ghostMessage.pop(k, None)

        threading.Thread(target=loop, daemon=True).start()

    def pushGhostMessage(this, last, threadId):
        if not last or not threadId or not this.isGhostStatus():
            return

        this.initDeleteMessage()

        msgId = getattr(last, "msgId", None)
        clientId = getattr(last, "clientId", None)
        if not msgId or not clientId:
            return

        k = f"{msgId}:{clientId}:{threadId}"
        this.ghostMessage[k] = {"msgId": msgId, "clientId": clientId, "threadId": threadId, "ts": time.time()}


class MessageHelper:
    def extractUids(this, data):
        m = getattr(data, "mentions", None)
        return [x["uid"] for x in m if isinstance(x, dict) and x.get("uid")] if m else []

    def normIds(this, userId):
        if userId is None:
            return []
        if isinstance(userId, (list, tuple, set)):
            return [str(x) for x in userId if x is not None]
        return [str(userId)]

    def buildMentionMessage(this, text, userId, type, userNameFunc):
        ids = this.normIds(userId)
        bodyText = str(text or "")

        if not ids:
            return bodyText, None

        if getattr(type, "name", None) != "GROUP":
            return bodyText, None

        names = [userNameFunc(uid) for uid in ids]
        head = f"@{names[0]}"
        mentions = [{"uid": ids[0], "pos": 0, "len": len(head)}]

        tokenRe = re.compile(r"@?u\{(\d+)\}|@?u(\d+)")
        tokens = []
        for m in tokenRe.finditer(bodyText):
            k = m.group(1) or m.group(2)
            if not k:
                continue
            idx = int(k) - 1
            if 0 <= idx < len(ids):
                tokens.append((m.start(), m.end(), idx))

        if tokens:
            out = []
            last = 0
            for s, e, idx in tokens:
                out.append(bodyText[last:s])
                out.append(f"@{names[idx]}")
                last = e
            out.append(bodyText[last:])
            bodyText = "".join(out)

        full = f"{head}\n{bodyText}" if bodyText else head
        base = len(head) + (1 if bodyText else 0)
        used = {ids[0]}

        for i in range(1, len(ids)):
            uid = ids[i]
            tag = f"@{names[i]}"
            p = full.find(tag, base)
            if p >= 0 and uid not in used:
                mentions.append({"uid": uid, "pos": p, "len": len(tag)})
                used.add(uid)

        return full, Mention(mentions)


class MessageFunctions:
    max_len = 1500
    _trCache = {}

    def getLang(this):
        s = ReadServices(this.uid) or {}
        return "vi" if bool(s.get("vi", True)) else "en"

    def getTransMap(this):
        for name in ("i18n", "I18N", "lang", "Lang", "langs", "Langs", "locale", "Locale", "translations", "Translations"):
            v = getattr(this, name, None)
            if isinstance(v, dict):
                return v
            v = globals().get(name)
            if isinstance(v, dict):
                return v
        return {}

    def buildTrCache(this, lang):
        mp = this.getTransMap()
        langMap = mp.get(lang) if isinstance(mp.get(lang), dict) else (mp.get("vi") if lang == "vi" and isinstance(mp.get("vi"), dict) else {})
        if not isinstance(langMap, dict):
            langMap = {}

        items = []
        for src, dst in langMap.items():
            if not isinstance(src, str) or "{" not in src or "}" not in src:
                continue

            parts = []
            names = []
            i = 0
            while True:
                a = src.find("{", i)
                if a < 0:
                    parts.append(src[i:])
                    break
                b = src.find("}", a + 1)
                if b < 0:
                    parts.append(src[i:])
                    break
                parts.append(src[i:a])
                n = src[a + 1:b].strip()
                names.append(n)
                parts.append(("__VAR__", n))
                i = b + 1

            if not names:
                continue

            pat = ["^"]
            for p in parts:
                if isinstance(p, tuple) and p[0] == "__VAR__":
                    pat.append(f"(?P<{p[1]}>.+?)")
                else:
                    pat.append(re.escape(p))
            pat.append("$")

            try:
                rx = re.compile("".join(pat))
            except Exception:
                continue

            items.append((rx, src, dst if isinstance(dst, str) and dst else src))

        MessageFunctions._trCache[lang] = items
        return items

    def reverseTr(this, text, lang):
        if not isinstance(text, str) or not text:
            return text

        items = MessageFunctions._trCache.get(lang)
        if items is None:
            items = this.buildTrCache(lang)

        for rx, src, dst in items:
            m = rx.match(text)
            if not m:
                continue
            d = m.groupdict()
            try:
                return dst.format(**d)
            except Exception:
                return dst
        return text

    def tr(this, text, lang=None):
        base = "" if text is None else str(text)
        s = ReadServices(this.uid) or {}
        if not bool(s.get("vi", True)):
            return base

        tfunc = getattr(this, "t", None)
        if not callable(tfunc):
            return base

        parts = base.splitlines(True)
        out = []
        for line in parts:
            nl = ""
            if line.endswith("\r\n"):
                body, nl = line[:-2], "\r\n"
            elif line.endswith("\n"):
                body, nl = line[:-1], "\n"
            elif line.endswith("\r"):
                body, nl = line[:-1], "\r"
            else:
                body = line

            try:
                trLine = tfunc(body, "vi")
                if trLine is None:
                    trLine = body
                else:
                    trLine = str(trLine)
            except Exception:
                trLine = body

            out.append(trLine + nl)

        return "".join(out)


    def getRecommended(this, data):
        return (getattr(getattr(data, "content", None), "title", "") or "") + " " if getattr(data, "msgType", None) == "chat.recommended" else ""

    def splitText(this, text, limit=None):
        limit = limit or this.max_len
        t = str(text or "")
        return [t[i:i + limit] for i in range(0, len(t), limit)] if t else [""]

    def makeStyle(this, n):
        return None

    def sendMention(this, text, userId, threadId, type):
        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(this.tr(text), userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(text=part, mention=mention if i == 0 else None, parse_mode="Markdown"),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last

    def sendReplyMention(this, text, userId, data, threadId, type):
        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(this.tr(text), userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(text=part, mention=mention if i == 0 else None, parse_mode="Markdown"),
                replyMsg=data if i == 0 else None,
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last

    def sendMMessage(this, text, userId, threadId, type):
        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(this.tr(text), userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(
                    text=part,
                    mention=mention if i == 0 else None,
                    style=None,
                    parse_mode="Markdown"
                ),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last
    
    def sendM(this, text, userId, threadId, type):
        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(this.tr(text), userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(
                    text=part,
                    mention=mention if i == 0 else None,
                    style=None,
                    parse_mode="Markdown"
                ),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last

    def sendMSuccess(this, text, userId, threadId, type):
        prefix = "<textsize=13>**++SUCCESS++**<textsize=13>"
        body = this.tr(text)
        full = f"{prefix}\n{body}" if body else prefix

        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(full, userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(
                    text=part,
                    mention=mention if i == 0 else None,
                    style=None,
                    parse_mode="Markdown"
                ),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last

    def sendMWarning(this, text, userId, threadId, type):
        prefix = "<textsize=13>**==WARNING==**<textsize=13>"
        body = this.tr(text)
        full = f"{prefix}\n{body}" if body else prefix

        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(full, userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(
                    text=part,
                    mention=mention if i == 0 else None,
                    style=None,
                    parse_mode="Markdown"
                ),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last

    def sendMFailed(this, text, userId, threadId, type):
        prefix = "<textsize=13>**!!FAILED!!**<textsize=13>"
        body = this.tr(text)
        full = f"{prefix}\n{body}" if body else prefix

        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(full, userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(
                    text=part,
                    mention=mention if i == 0 else None,
                    style=None,
                    parse_mode="Markdown"
                ),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last

    def sendCooldown(this, count, data, threadId, type):
        for i in range(count, 0, -1):
            this.sendMultiReaction(data, "🕑", threadId, type, 102229, numreact=i)
            time.sleep(1)
            this.sendMultiReaction(data, "", threadId, type, -1, numreact=i)

    def sendMCustom(this, custom, color, text, userId, threadId, type):
        if color == "g" or color == "green":
            custom = f"++{custom}++"
        elif color == "y" or color == "yellow":
            custom = f"=={custom}=="
        elif color == "r" or color == "red":
            custom = f"!!{custom}!!"

        prefix = f"<textsize=13>**{custom}**<textsize=13>"
        body = this.tr(text)
        full = f"{prefix}\n{body}" if body else prefix

        helper = MessageHelper()
        fullText, mention = helper.buildMentionMessage(full, userId, type, this.userName)
        parts = this.splitText(fullText)

        last = None
        for i, part in enumerate(parts):
            last = this.send(
                message=Message(
                    text=part,
                    mention=mention if i == 0 else None,
                    style=None,
                    parse_mode="Markdown"
                ),
                threadId=threadId,
                type=type
            )
            if hasattr(this, "pushGhostMessage"):
                this.pushGhostMessage(last, threadId)
        return last
