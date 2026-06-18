
from dto.index import *

TimeoutSec = 25
UserAgent = "Mozilla/5.0"

def H(extra=None):
    h = {"User-Agent": UserAgent, "Accept": "application/json,*/*", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h

def Norm(s):
    return (s or "").strip()

def Clip(s, n=12000):
    return (s or "")[:n]

def BuildPayload(raw):
    raw = Norm(raw)
    if not raw:
        return {}
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except:
            return {}
    return {"data": {"url": raw, "unlock": True}}

def ToCurl(method, url, headers, payload=None):
    hs = []
    for k, v in (headers or {}).items():
        if v:
            hs.append(f"-H {shlex.quote(f'{k}: {v}')}")
    data = ""
    if payload is not None and method.upper() != "GET":
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload, ensure_ascii=False)
        data = f" --data {shlex.quote(str(payload))}"
    return f"curl -X {method.upper()} {shlex.quote(url)} {' '.join(hs)}{data}".strip()

def RunShell(cmd, timeout=TimeoutSec, maxBytes=24000):
    if os.name == "nt":
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    else:
        p = subprocess.run(cmd, shell=True, executable="/bin/bash", capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    if not out:
        out = f"exit={p.returncode}"
    return out[:maxBytes]

def hookSystem(this, message, data, userId, threadId, type):
    raw = Norm(getattr(message, "text", ""))
    if not this.mainBot:
        return this.sendMWarning(f"Only server can use {this.rawCommand}..!", userId, threadId, type)

    marker = ":sys"
    if marker in raw:
        idx = raw.find(marker)
        cmd = Norm(raw[idx + len(marker):])
        if not cmd:
            return this.sendMWarning("Missing cmd", userId, threadId, type)
        cmd = cmd.replace(" and ", " && ").replace(" AND ", " && ").replace("\nand ", "\n&& ").replace("\nAND ", "\n&& ")
        try:
            out = RunShell(cmd)
            return this.sendMWarning(Clip(out), userId, threadId, type)
        except Exception as e:
            return this.sendMWarning(f"Error: {e}", userId, threadId, type)

    try:
        args = shlex.split(raw)
    except:
        args = raw.split()

    if len(args) < 2:
        return this.sendMWarning("hookler..!", userId, threadId, type)

    target = args[1]
    isUrl = target.startswith("http://") or target.startswith("https://")

    if isUrl:
        payloadRaw = ""
        respMode = "json"
        timing = False
        postCheck = False
        verbose = False
        curl = False
        scrap = False
        method = "POST"
        ua = UserAgent
        accept = "application/json,*/*"
        ct = "application/json"

        i = 2
        while i < len(args):
            a = args[i]
            if a in ("--post",):
                method = "POST"
                postCheck = True
                i += 1
                continue
            if a in ("--timing",):
                timing = True
                i += 1
                continue
            if a in ("--verbose", "-v"):
                verbose = True
                i += 1
                continue
            if a == "--curl":
                curl = True
                i += 1
                continue
            if a in ("--scrap", "--scrape", "--get"):
                scrap = True
                method = "GET"
                i += 1
                continue
            if a == "--method":
                if i + 1 < len(args):
                    method = (args[i + 1] or "POST").upper()
                    i += 2
                    continue
                i += 1
                continue
            if a == "--ua":
                if i + 1 < len(args):
                    ua = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a == "--accept":
                if i + 1 < len(args):
                    accept = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a == "--ct":
                if i + 1 < len(args):
                    ct = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a == "--response":
                if i + 1 < len(args):
                    respMode = (args[i + 1] or "json").lower()
                    i += 2
                    continue
                i += 1
                continue
            payloadRaw = a
            i += 1

        t0 = time.time()
        try:
            if scrap or method.upper() == "GET":
                r = requests.get(target, headers={"User-Agent": ua, "Accept": "*/*"}, timeout=TimeoutSec)
                dt = int((time.time() - t0) * 1000)
                if curl:
                    return this.sendMSuccess(Clip(ToCurl("GET", target, {"User-Agent": ua, "Accept": "*/*"})), userId, threadId, type)
                if postCheck:
                    ok = 200 <= r.status_code < 300
                    msg = f"GET <response[{r.status_code}]> {'OK' if ok else 'FAILED'}"
                    if timing:
                        msg += f" - {dt}ms"
                    return this.sendMSuccess(msg, userId, threadId, type)

                out = r.text or ""
                if respMode == "status":
                    out = f"status={r.status_code}"
                elif respMode == "headers":
                    out = json.dumps(dict(r.headers), ensure_ascii=False, indent=2)
                if verbose:
                    out = f"[GET]\nurl={target}\nstatus={r.status_code}\nlen={len(r.content or b'')}\nct={r.headers.get('content-type','')}\n\n{out}"
                if timing:
                    out = f"{out}\n\n{dt}ms"
                return this.sendMSuccess(Clip(out), userId, threadId, type)

            payload = BuildPayload(payloadRaw)
            headers = H({"User-Agent": ua, "Accept": accept, "Content-Type": ct})
            r = requests.request(method.upper(), target, json=payload, headers=headers, timeout=TimeoutSec)
            dt = int((time.time() - t0) * 1000)

            if curl:
                return this.sendMSuccess(Clip(ToCurl(method, target, headers, payload)), userId, threadId, type)

            if postCheck:
                ok = 200 <= r.status_code < 300
                msg = f"{method.upper()} <response[{r.status_code}]> {'OK' if ok else 'FAILED'}"
                if timing:
                    msg += f" - {dt}ms"
                return this.sendMSuccess(msg, userId, threadId, type)

            if respMode == "status":
                out = f"status={r.status_code}"
            elif respMode == "headers":
                out = json.dumps(dict(r.headers), ensure_ascii=False, indent=2)
            elif respMode == "text":
                out = r.text or ""
            elif respMode == "all":
                try:
                    dataOut = r.json()
                except:
                    dataOut = r.text
                out = json.dumps({"status": r.status_code, "headers": dict(r.headers), "data": dataOut}, ensure_ascii=False, indent=2)
            else:
                try:
                    out = json.dumps(r.json(), ensure_ascii=False, indent=2)
                except:
                    out = r.text or ""

            if verbose:
                out = f"[{method.upper()}]\nurl={target}\nstatus={r.status_code}\nlen={len(r.content or b'')}\nct={r.headers.get('content-type','')}\n\n{out}"
            if timing:
                out = f"{out}\n\n{dt}ms"
            return this.sendMSuccess(Clip(out), userId, threadId, type)

        except Exception as e:
            return this.sendMWarning(f"Error: {e}", userId, threadId, type)

    return this.sendMWarning("Invalid target", userId, threadId, type)

dependencies = {
    "name": "hook",
    "permission": 3,
    "description": "Hook",
    "cooldown": 5,
    "main": hookSystem
}
