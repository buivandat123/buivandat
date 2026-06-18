from functions.services.artistcore.listUser import DrawList
from functions.services.hook.core_hook.extra_multibot_core import *

def SafeRemove(p):
    try:
        if p and os.path.exists(p):
            os.remove(p)
    except:
        pass

def GetAvatar(this, uid):
    try:
        if hasattr(this, "getUserAvatar"):
            a = this.getUserAvatar(uid)
            if a:
                return a
    except:
        pass
    try:
        info = this.fetchUserInfo(uid)
        p = info.changed_profiles.get(uid)
        if isinstance(p, dict):
            return p.get("avatar") or p.get("thumbSrc") or ""
        return getattr(p, "avatar", "") or getattr(p, "thumbSrc", "") or ""
    except:
        return ""

def ListBots(this, message, data, userId, threadId, type):
    arr = BuildBotIndexList()
    if not arr:
        return SendMention(this, "No bots found", userId, threadId, type)

    now = datetime.now()

    def ParseTime(s):
        try:
            return datetime.strptime(str(s), "%H:%M:%S-%d/%m/%Y")
        except:
            return None

    def StatusText(b):
        if "isActived" not in b:
            return "Non Active"
        exp = ParseTime(b.get("expiredTime"))
        if exp and now > exp:
            return "Expired"
        return "Active" if b.get("status") else "Inactive"

    ownerUid = str(this.uid)
    owner = {
        "uid": ownerUid,
        "name": this.userName(ownerUid),
        "role": "Owner",
        "avatar": GetAvatar(this, ownerUid)
    }

    admins = []
    for i, (b, _, meta) in enumerate(arr, 1):
        if not isinstance(b, dict):
            continue
        if b.get("mainBot"):
            continue

    admins = []
    for i, (b, _, meta) in enumerate(arr, 1):
        if not isinstance(b, dict):
            continue
        if b.get("mainBot"):
            continue

        userClientId = str(b.get("clientBotId") or "")
        name = str(b.get("username") or "Unknown")
        role = StatusText(b)
        print(userClientId)

        admins.append({
            "uid": userClientId,
            "name": name,
            "role": role,
            "avatar": GetAvatar(this, userClientId) if userClientId else ""
        })

    imagePath = f"assets/cache/bot_list_{threadId}_{int(time.time()*1000)}.png"
    try:
        outPath, w, h = DrawList(
            Owner=owner,
            Admins=admins,
            OutPath=imagePath,
            Title=None,
            SubTitle=None,
            Source="Bot Manager",
            ItemsPerPage=10
        )

        up = this.uploadImage(outPath, threadId, type)
        hd = up.get("hdUrl")
        SafeRemove(outPath)
        if hd:
            name = this.userName(userId)
            return this.sendImage(
                imageUrl=hd,
                message=Message(text=f"{name}", mention=Mention(userId, offset=0, length=len(name))),
                threadId=threadId,
                type=type,
                width=w,
                height=h
            )
    except:
        SafeRemove(imagePath)

    out = "All bots on server:\n"
    for i, (b, _, __) in enumerate(arr, 1):
        if not isinstance(b, dict):
            continue
        if b.get("mainBot"):
            continue

        st = StatusText(b)
        out += f"{i}. {b.get('username')}{f' - {st}' if st else ''}\n"
        out += f"   botIntId: {b.get('botIntId')}\n"
        out += f"   Prefix: {b.get('prefix')}\n"
        if b.get("expiredTime"):
            out += f"   Expires: {b.get('expiredTime')}\n"

    return SendMention(this, out, userId, threadId, type)