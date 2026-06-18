from dto.index import *
from functions.services.artistcore.drawQr import DrawBank, BANK_ALIASES



BANKS = set(BANK_ALIASES.values())


def QrbPack(acc, owner, bank, note, amount):
    return {
        "acc": str(acc or "").strip(),
        "owner": str(owner or "").strip(),
        "bank": str(bank or "").strip(),
        "note": "" if note is None else str(note),
        "amount": "" if amount is None else str(amount),
    }


def QrbValid(x):
    return all((x.get("acc"), x.get("owner"), x.get("bank")))


def IsDigits(x):
    s = str(x or "").strip()
    return bool(s) and s.isdigit()


def NormalizeBank(x):
    k = str(x or "").strip().upper().replace("-", "_")
    return BANK_ALIASES.get(k) or ""


def FindBankIndex(tokens):
    for i, t in enumerate(tokens):
        bank = NormalizeBank(t)
        if bank:
            return i, bank
    return -1, ""


def ParseQrbArgs(args):
    a = [str(x) for x in (args or []) if str(x).strip()]
    if not a or not IsDigits(a[0]):
        return None, "Wrong account number"

    acc = a[0]
    body = a[1:]
    if not body:
        return None, "Blank Owner and Bank"

    bi, bank = FindBankIndex(body)
    if bi < 0:
        return None, "Invalid supported bank"

    ownerTokens = body[:bi]
    tail = body[bi + 1 :]

    if not ownerTokens:
        return None, "Blank owner"

    amount = ""
    noteTokens = tail
    if tail and IsDigits(tail[-1]):
        amount = tail[-1]
        noteTokens = tail[:-1]

    owner = " ".join(ownerTokens).strip()
    note = " ".join(noteTokens).strip()

    return QrbPack(acc, owner, bank, note, amount), None


def qrbank(this, message, data, userId, threadId, type):
    txt = (message.text or "").strip()
    raw = txt.split()
    args = raw[1:] if raw else []

    saveFlag = "--save" in args
    args = [x for x in args if x != "--save"]

    cfg = ReadServices(this.uid)
    saved = cfg.get("saved") if isinstance(cfg, dict) else None

    usage = f"Use {this.prefix}{this.rawCommand} STK CHUTK BANK ND AMOUNT --save (vd: VCB, TPB, BIDV...)"

    if not args:
        if not (isinstance(saved, dict) and QrbValid(saved)):
            return this.sendMWarning(usage, userId, threadId, type)
        p = saved
    else:
        p, err = ParseQrbArgs(args)
        if err:
            return this.sendMWarning(f"{err}\n{usage}", userId, threadId, type)

    if saveFlag:
        WriteService(this.uid, {"saved": p, "ts": int(time.time())})

    outName = f"qrbank_{threadId}_{int(time.time()*1000)}.png"
    ava = this.getUserAvatar(userId) if hasattr(this, "getUserAvatar") else ""

    fp = DrawBank(
        p["owner"],
        p["acc"],
        p["owner"],
        p["bank"],
        p["note"],
        ava,
        outName,
        p["amount"]
    )
    if not fp:
        return

    w = h = None
    try:
        im = Image.open(fp)
        w, h = im.size
        im.close()
    except:
        pass

    up = this.uploadImage(fp, threadId, type) or {}
    try:
        os.remove(fp)
    except:
        pass

    hd = up.get("hdUrl")
    if not hd:
        return

    this.sendMSuccess(None, userId,threadId,type)
    this.sendImage(
        imageUrl=hd,
        message=Message(text=None),
        threadId=threadId,
        type=type,
        width=w,
        height=h
    )


dependencies = {
    "name": "qrbank",
    "permission": 0,
    "cooldown": 7,
    "description": "Generate payment code",
    "main": qrbank
}