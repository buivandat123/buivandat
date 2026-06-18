from functions.services.artistcore.codePreview import *
from dto.index import *

def Norm(s):
    return (s or "").strip()

def GetAny(o, k, d=None):
    if o is None:
        return d
    if isinstance(o, dict):
        return o.get(k, d)
    return getattr(o, k, d)

def GetStr(o, k, d=""):
    v = GetAny(o, k, d)
    if v is None:
        return d
    return v if isinstance(v, str) else str(v)

def PickContentText(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        v = content.get("title") or content.get("text") or ""
        return v if isinstance(v, str) else (str(v) if v is not None else "")
    v = getattr(content, "title", None)
    if isinstance(v, str) and v:
        return v
    v = getattr(content, "text", None)
    if isinstance(v, str) and v:
        return v
    return ""

def GetQuoteText(data):
    q = GetAny(data, "quote", None)
    if q is None:
        return ""
    if isinstance(q, dict):
        return q.get("msg") or ""
    return GetStr(q, "msg", "")

def GetMsgText(message, data):
    t = GetStr(data, "msg", "")
    if t:
        return t
    t = GetStr(message, "msg", "")
    if t:
        return t
    t = PickContentText(GetAny(message, "content", None))
    if t:
        return t
    t = PickContentText(GetAny(data, "content", None))
    if t:
        return t
    return GetStr(message, "text", "")

def GetRawArgs(message, data):
    t = GetMsgText(message, data)
    m = re.match(r"^\S+\s*(.*)$", t, flags=re.S)
    return m.group(1) if m else ""

def SaveTmpPng(pngBytes):
    os.makedirs("assets/cache", exist_ok=True)
    fn = f"assets/cache/viewcode_{int(time.time()*1000)}.png"
    with open(fn, "wb") as f:
        f.write(pngBytes)
    return fn

def GuessLangTitle(code, fallback="Snippet"):
    s = (code or "").strip()
    if not s:
        return fallback
    low = s.lower()
    if "print(" in low or "def " in low or "import " in low:
        return "Python"
    if "#include" in low or "std::" in low:
        return "Cpp"
    if "console.log" in low or "function " in low or "=>" in low:
        return "JavaScript"
    try:
        lx = guess_lexer(s)
        n = getattr(lx, "name", "") or ""
        n = n if isinstance(n, str) else str(n)
        nl = n.lower()
        if not n or "text" in nl or "plain" in nl:
            return fallback
        name = re.sub(r"\s+", "", n)
        name = re.sub(r"[^A-Za-z0-9_+\-\.]+", "", name)[:24]
        return name or fallback
    except:
        return fallback

def ReadFileText(path):
    try:
        with open(path, "rb") as f:
            b = f.read()
        for enc in ("utf-8", "utf-8-sig", "cp1252"):
            try:
                return b.decode(enc)
            except:
                pass
        return b.decode("latin-1", errors="replace")
    except:
        return None

def SafePath(p):
    p = Norm(p).strip("\"'").replace("\\", "/")
    if not p or "\x00" in p:
        return None
    if p.startswith("../") or "/../" in p or p.startswith("..\\") or "\\..\\" in p:
        return None
    if p.startswith("/") or re.match(r"^[a-zA-Z]:/", p):
        return p
    return p

def ExtractCode(message, data):
    raw = GetRawArgs(message, data)
    if Norm(raw):
        return raw, None
    q = GetQuoteText(data)
    return (q, None) if Norm(q) else ("", None)

def ViewCodeCommand(this, message, data, userId, threadId, type):
    arg = GetRawArgs(message, data)
    q = GetQuoteText(data)

    isFile = False
    fp = None
    if Norm(arg) and "\n" not in arg:
        cand = SafePath(arg)
        if cand:
            fp = cand
            isFile = True

    if isFile:
        if not this.mainBot:
            this.sendMWarning(f"Only server can use {this.rawCommand}..!", userId, threadId, type)
            return
        txt = ReadFileText(fp)
        if txt is None:
            return this.sendMFailed("File not found or unreadable.", userId, threadId, type)
        title = os.path.basename(fp) or "Snippet"
        png, w, h = RenderCodeToBytes(txt, title)
    else:
        code = arg if Norm(arg) else q
        if not Norm(code):
            return this.sendMWarning("Give me code or quote it.", userId, threadId, type)
        title = GuessLangTitle(code, "Snippet")
        png, w, h = RenderCodeToBytes(code, title)

    imagePath = SaveTmpPng(png)
    imageup = this.uploadImage(imagePath, threadId, type)
    hd = imageup.get("hdUrl") if isinstance(imageup, dict) else None
    try:
        os.remove(imagePath)
    except:
        pass
    if not hd:
        return None

    name = this.userName(userId)
    return this.sendImage(
        imageUrl=hd,
        message=Message(text=f"{name}", mention=Mention(userId, offset=0, length=len(name))),
        threadId=threadId,
        type=type,
        width=w,
        height=h
    )

dependencies = {
    "name": "viewcode",
    "permission": 3,
    "description": "Render code",
    "cooldown": 5,
    "main": ViewCodeCommand
}