from functions.services.hook.bot_hook.execs_core import *
import re, json, builtins, traceback, ipaddress, requests
from urllib.parse import urlparse

maxlen = 10_000_000
urlfullre = re.compile(r"(https?://\S+)$")

def Clip(s, limit=maxlen):
    if s is None:
        return ""
    s = str(s)
    return s[:limit] + ("\n..." if len(s) > limit else "")

def StripFence(s):
    s = ("" if s is None else str(s)).strip()
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return s

def ExtractUrl(s):
    s = ("" if s is None else str(s)).strip()
    if not s or "\n" in s:
        return ""
    m = urlfullre.fullmatch(s)
    if not m:
        return ""
    return m.group(1).rstrip(").,;\"'")

def IsBlockedHost(host):
    if not host:
        return True
    h = host.lower().strip(".")
    if h == "localhost" or h.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(h)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
    except:
        return False

def SafeFetch(url):
    try:
        p = urlparse(url)
        if p.scheme not in {"http", "https"}:
            return None
        if IsBlockedHost(p.hostname or ""):
            return None

        r = requests.get(url, timeout=6, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        limit = 1024 * 1024
        buf = bytearray()

        for chunk in r.iter_content(chunk_size=16384):
            if not chunk:
                continue
            buf.extend(chunk)
            if len(buf) >= limit:
                break

        ct = (r.headers.get("content-type") or "").lower()
        textok = ("application/json" in ct) or ct.startswith("text/") or ("xml" in ct) or ("javascript" in ct)

        if textok:
            enc = r.encoding or "utf-8"
            txt = bytes(buf).decode(enc, errors="replace")
            if len(buf) >= limit:
                txt += "\n..."
            return txt

        return f"fetched: content-type={ct or 'unknown'} bytes={len(buf)}"
    except:
        return None

def TryLoadJsonString(s, limit=2_000_000):
    if not isinstance(s, str):
        return None
    t = StripFence(s).strip()
    if not t or len(t) > limit:
        return None
    if (t[0] == "{" and t[-1] == "}") or (t[0] == "[" and t[-1] == "]"):
        try:
            return json.loads(t)
        except:
            return None
    return None

def DeepParseJson(obj, depth=4):
    if depth <= 0:
        return obj

    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out[k] = DeepParseJson(v, depth)
        return out

    if isinstance(obj, list):
        return [DeepParseJson(x, depth) for x in obj]

    if isinstance(obj, str):
        loaded = TryLoadJsonString(obj)
        if loaded is not None:
            return DeepParseJson(loaded, depth - 1)
        return obj

    return obj

def PrettyJson(obj):
    try:
        if isinstance(obj, (dict, list)):
            return json.dumps(DeepParseJson(obj, 4), ensure_ascii=False, indent=2)

        s = StripFence(obj)
        t = s.strip()
        if not t:
            return s
        if len(t) > 2_000_000:
            return s

        loaded = TryLoadJsonString(t)
        if loaded is not None:
            return json.dumps(DeepParseJson(loaded, 4), ensure_ascii=False, indent=2)

        return s
    except:
        return StripFence(obj)

def Normalize(obj):
    if isinstance(obj, str):
        url = ExtractUrl(obj)
        if url:
            fetched = SafeFetch(url)
            if fetched is not None:
                obj = fetched
    return Clip(PrettyJson(obj))

def BuildCtx(this, data, userId, threadId, type, send):
    return {
        "this": this,
        "api": this,
        "Message": Message,
        "threadId": threadId,
        "tid": threadId,
        "type": type,
        "BuiltinType": builtins.type,
        "ThreadType": ThreadType,
        "userId": userId,
        "data": data,
        "send": lambda m: send(Normalize(m)),
        "Mention": Mention,
        "print": lambda *a, **k: send(" ".join(map(str, a))),
    }

def GetRawCode(message, data):
    text = (getattr(message, "text", "") or "").strip()
    quotemsg = (getattr(getattr(data, "quote", None), "msg", None) or "").strip()
    parts = text.split(maxsplit=1)
    return (parts[1].strip() if len(parts) > 1 else quotemsg)

def RunEval(this, raw, ctx, send):
    lang, code = decLa(raw)

    if lang == "py":
        res, err = pyexec(code, ctx)
        if err:
            return send("error:\n" + Normalize(err))
        if res is not None:
            return send(Normalize(res))
        return None

    try:
        if lang == "js":
            rc, out, err = javascriptRun(code, timeout=6)
        elif lang == "cpp":
            rc, out, err = cppgpp(code, timeout=12)
        else:
            return send("Unsupported language")

        if err:
            return send("error:\n" + Normalize(hidefile(err)))
        return send(Normalize(out if out else f"exit={rc}"))
    except Exception:
        return send("error:\n" + Normalize(hidefile(traceback.format_exc(limit=5))))

def EvalCommand(this, message, data, userId, threadId, type):
    raw = GetRawCode(message, data)
    if not raw:
        return this.sendMWarning("What do you wanna run..?", userId, threadId, type)

    send = lambda m: this.sendMSuccess(str(m), userId, threadId, type)
    ctx = BuildCtx(this, data, userId, threadId, type, send)
    return RunEval(this, raw, ctx, send)

dependencies = {
    "name": "eval",
    "permission": 3,
    "description": "Eval Exec",
    "cooldown": 5,
    "main": EvalCommand
}