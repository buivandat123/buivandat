import os
import time
import threading
from datetime import datetime
from rich.console import Console
from rich.text import Text

def Clamp255(v):
    v = int(v)
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v

def Lerp(a, b, t):
    return a + (b - a) * t

def GradientRender(text, startRgb, endRgb, spread=1.0):
    sr, sg, sb = startRgb
    er, eg, eb = endRgb
    chars = str(text or "")
    n = len(chars)
    if n <= 1:
        return Text(chars, style=f"rgb({Clamp255(sr)},{Clamp255(sg)},{Clamp255(sb)})")

    den = (n - 1) / (float(spread) if spread and spread > 0 else 1.0)
    out = Text()
    for i, ch in enumerate(chars):
        x = i / den
        if x < 0:
            x = 0.0
        elif x > 1:
            x = 1.0
        r = Clamp255(Lerp(sr, er, x))
        g = Clamp255(Lerp(sg, eg, x))
        b = Clamp255(Lerp(sb, eb, x))
        out.append(ch, style=f"rgb({r},{g},{b})")
    return out

class Logging:
    def __init__(this, theme="default", formatTime="%H:%M:%S", appName="app"):
        this.reset = "\x1b[0m"
        this.theme = str(theme or "default").lower()
        this.formatTime = formatTime
        this.appName = str(appName or "app")

        this.debugFile = "assets/log/debug.log"
        this.errorFile = "assets/log/error.log"

        this.colors = this.LoadScheme(this.theme)
        this.levels = this.MapLevel()

        this.console = Console()
        grad = this.colors.get("grad") or {}
        this.gradTime = grad.get("dim")
        this.gradLevel = grad.get("tag")
        this.gradText = grad.get("text")
        this.gradMeta = grad.get("sub")
        this.grad = bool(grad)

        this.lock = threading.Lock()

    def LoadScheme(this, theme):
        theme = str(theme or "default").lower()
        schemes = {
            "default": {
                "time": "\x1b[38;5;240m",
                "level": "\x1b[38;5;250m",
                "meta": "\x1b[38;5;245m",
                "text": "\x1b[38;5;252m",
            },
            "glass": {
                "grad": {
                    "dim": ((170, 175, 185), (240, 242, 246)),
                    "sub": ((185, 190, 205), (255, 255, 255)),
                    "tag": ((210, 214, 222), (255, 255, 255)),
                    "text": ((215, 218, 225), (255, 255, 255)),
                },
            },
        }
        return schemes.get(theme, schemes["default"])

    def MapLevel(this):
        return {
            "info": "INFO",
            "debug": "DEBUG",
            "success": "SUCCESS",
            "login": "LOGIN",
            "warning": "WARNING",
            "notice": "NOTICE",
            "base": "BASE",
            "client": "CLIENT",
            "event": "EVENT",
            "start": "START",
            "stop": "STOP",
            "critical": "CRITICAL",
            "error": "ERROR",
            "message": "MESSAGE",
        }

    def Timenow(this):
        return time.strftime(this.formatTime, time.localtime())

    def Unixstamp(this):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def AppendFile(this, path, levelTag, text, stamp):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {levelTag} in {this.appName}: {text}\n")

    def BuildHead(this, lines, meta=None):
        prefix = []
        if meta:
            bot = meta.get("bot")
            groupName = meta.get("group_name")
            groupId = meta.get("group_id")
            userName = meta.get("user_name")
            userId = meta.get("user_id")
            ref = meta.get("ref")

            if bot:
                prefix.append(f"[{bot}]")
            if groupName:
                prefix.append(f"[{groupName}{f' - {groupId}' if groupId else ''}]")
            if userName:
                prefix.append(f"{userName}{f' - {userId}' if userId else ''}")
            if ref:
                prefix.append(f"-> {ref}")

        head = " ".join(prefix).strip()
        if head:
            return f"{head}: {lines[0]}"
        return lines[0]

    def RichWerkzeugLine(this, timeStr, levelStr, message):
        line = Text()
        timeTxt = GradientRender(f"[{timeStr}]", this.gradTime[0], this.gradTime[1], 1.2) if this.gradTime else Text(f"[{timeStr}]")
        levelTxt = GradientRender(levelStr, this.gradLevel[0], this.gradLevel[1], 1.0) if this.gradLevel else Text(levelStr)
        metaTxt = GradientRender(f"in {this.appName}:", this.gradMeta[0], this.gradMeta[1], 1.0) if this.gradMeta else Text(f"in {this.appName}:")
        msgTxt = GradientRender(message, this.gradText[0], this.gradText[1], 1.45) if this.gradText else Text(message)

        line.append_text(timeTxt)
        line.append(" ")
        line.append_text(levelTxt)
        line.append(" ")
        line.append_text(metaTxt)
        line.append(" ")
        line.append_text(msgTxt)
        return line

    def Emit(this, levelTag, lines, kindLog=None, meta=None):
        timeStr = this.Timenow()
        head = this.BuildHead(lines, meta)

        if this.grad:
            this.console.print(this.RichWerkzeugLine(timeStr, levelTag, head))
            for x in lines[1:]:
                this.console.print(this.RichWerkzeugLine(timeStr, levelTag, str(x)))
        else:
            base = this.colors
            print(
                f"{base['time']}[{timeStr}]{this.reset} "
                f"{base['level']}{levelTag}{this.reset} "
                f"{base['meta']}in {this.appName}:{this.reset} "
                f"{base['text']}{head}{this.reset}"
            )
            for x in lines[1:]:
                print(
                    f"{base['time']}[{timeStr}]{this.reset} "
                    f"{base['level']}{levelTag}{this.reset} "
                    f"{base['meta']}in {this.appName}:{this.reset} "
                    f"{base['text']}{x}{this.reset}"
                )

        stamp = this.Unixstamp()
        storePlain = "\n".join(lines)

        if kindLog == "debug":
            with this.lock:
                this.AppendFile(this.debugFile, levelTag, storePlain, stamp)
            return

        if levelTag in ("ERROR", "CRITICAL") or kindLog == "error":
            with this.lock:
                this.AppendFile(this.errorFile, levelTag, storePlain, stamp)

    def fnLogger(this, level, text, kindLog=None, meta=None):
        lvl = str(level or "notice").lower()
        tag = this.levels.get(lvl, "NOTICE")
        lines = str("" if text is None else text).splitlines() or [""]
        this.Emit(tag, lines, kindLog=kindLog, meta=meta)

    def info(this, text): this.fnLogger("info", text, kindLog="debug")
    def debug(this, text): this.fnLogger("debug", text, kindLog="debug")
    def client(this, text): this.fnLogger("client", text)
    def success(this, text): this.fnLogger("success", text)
    def base(this, text): this.fnLogger("base", text)
    def login(this, text): this.fnLogger("login", text)
    def warning(this, text): this.fnLogger("warning", text)
    def notice(this, text): this.fnLogger("notice", text)
    def event(this, text): this.fnLogger("event", text)
    def start(this, text): this.fnLogger("start", text)
    def stop(this, text): this.fnLogger("stop", text)
    def critical(this, text): this.fnLogger("critical", text, kindLog="error")
    def error(this, text): this.fnLogger("error", text, kindLog="error")
    def errorMeta(this, text, meta=None): this.fnLogger("error", text, kindLog="error", meta=meta)

logger = Logging(theme="glass", appName="bot")