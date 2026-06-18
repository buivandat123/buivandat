from dto.index import *

def toText(data):
    if data is None:
        return "null"
    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)

def locketGold(username: str):
    req = urequest.Request(
        url="https://tight-voice-f21c.quandev2k7.workers.dev/",
        data=json.dumps({"username": username}).encode(),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "ryanzola",
            "User-Agent": "python-urllib/1.0",
        },
    )

    try:
        with urequest.urlopen(req, timeout=20) as res:
            raw = res.read().decode("utf-8", "replace")
            ct = (res.headers.get("Content-Type") or "").lower()

            if "application/json" in ct:
                try:
                    data = json.loads(raw)
                except:
                    data = {"ok": True, "data": raw}
            else:
                data = {"ok": True, "data": raw}

            if isinstance(data, dict):
                data.setdefault("ok", True)
                data.setdefault("status", getattr(res, "status", 200))
            return data

    except uerror.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data.setdefault("ok", False)
                data.setdefault("status", e.code)
            return data
        except:
            return {"ok": False, "status": e.code, "error": raw}

    except Exception as e:
        return {"ok": False, "error": str(e)}

def locketRyan(this, message, data, userId, threadId, type):
    cmd = (message.text or "").split(maxsplit=1)
    if len(cmd) < 2:
        return this.sendMWarning(
            f"Use {this.prefix}{this.rawCommand} with a username behind to upgrade locket",
            userId, threadId, type
        )

    result = locketGold(cmd[1])
    return this.sendMSuccess(toText(result), userId, threadId, type)

dependencies = {
    "name": "locket",
    "permission": 0,
    "description": "Upgrade locket gold for user",
    "cooldown": 5,
    "main": locketRyan
}