from dto.index import *
from functions.services.artistcore.listUser import DrawList

def BuildAdminList(this, settings, threadId):
    me = str(this.uid)

    if not isinstance(settings, dict):
        settings = {}

    groupAdmin = settings.get("groupAdmin")
    if not isinstance(groupAdmin, dict):
        groupAdmin = {}

    def NormList(v):
        if not isinstance(v, (list, tuple, set)):
            return []
        out = []
        for x in v:
            s = str(x or "").strip()
            if s:
                out.append(s)
        return out

    def GetAvatar(uid):
        a = None
        try:
            a = this.getAvatar(uid)
        except:
            a = None

        if isinstance(a, dict):
            return str(a.get("bk_full_avatar") or a.get("avatar") or a.get("thumbSrc") or "")
        return str(getattr(a, "bk_full_avatar", "") or getattr(a, "avatar", "") or getattr(a, "thumbSrc", "") or "")

    hi = NormList(settings.get("highAdmin"))
    bot = NormList(settings.get("adminBot"))
    grp = NormList(groupAdmin.get(threadId))

    hiSet = set(hi)
    bot = [x for x in bot if x not in hiSet]
    botSet = set(bot)
    grp = [x for x in grp if x not in hiSet and x not in botSet]

    owner = {
        "uid": me,
        "name": this.userName(me),
        "role": "Owner",
        "avatar": GetAvatar(me)
    }

    seen = {me}
    out = []

    def Push(uid, role):
        uid = str(uid or "").strip()
        if not uid or uid in seen:
            return
        seen.add(uid)
        out.append({
            "uid": uid,
            "name": this.userName(uid),
            "role": role,
            "avatar": GetAvatar(uid)
        })

    for uid in hi:
        Push(uid, "High Admin")
    for uid in bot:
        Push(uid, "Bot Admin")
    for uid in grp:
        Push(uid, "Group admin")

    rank = {"High Admin": 0, "Bot Admin": 1, "Group admin": 2}
    out.sort(key=lambda x: (rank.get(x.get("role"), 9), (x.get("name") or "").lower()))
    return owner, out, len(hi), len(bot), len(grp)


def SendAdminListImage(this, owner, admins, threadId, type, targetUid):
    imagePath = f"assets/cache/admin_list_{threadId}_{int(time.time()*1000)}.png"
    outPath, w, h = DrawList(
        Owner=owner,
        Admins=admins,
        OutPath=imagePath,
        Title=None,
        SubTitle=None,
        Source="Admin Manager",
        ItemsPerPage=10
    )

    up = this.uploadImage(outPath, threadId, type) or {}
    if not isinstance(up, dict):
        up = {}
    hd = up.get("hdUrl")

    try:
        if outPath and os.path.exists(outPath):
            os.remove(outPath)
    except:
        pass

    if not hd:
        return False

    name = this.userName(targetUid)
    this.sendImage(
        imageUrl=hd,
        message=Message(text=f"{name}", mention=Mention(targetUid, offset=0, length=len(name))),
        threadId=threadId,
        type=type,
        width=w,
        height=h
    )
    return True


def SendAdminListText(this, admins, userId, threadId, type, hCount, bCount, gCount):
    if not admins:
        return this.sendMWarning("Admin list is empty", userId, threadId, type)

    buckets = [("High Admin", hCount), ("Bot Admin", bCount), ("Group admin", gCount)]
    out = ["Admin list", ""]

    for role, cnt in buckets:
        if not cnt:
            continue

        out.append(f"{role}:")
        i = 0

        for a in admins:
            if a.get("role") != role:
                continue
            i += 1
            out.append(f"{i}. {a.get('name')}")

        out.append("")

    return this.sendMSuccess("\n".join(out).strip(), userId, threadId, type)


def ParseLevel(parts):
    action = None
    level = 1

    if len(parts) >= 2 and parts[1].lower() in ("add", "remove"):
        action = parts[1].lower()
        if len(parts) >= 3 and parts[2].isdigit():
            return action, int(parts[2])
        return None, None

    if len(parts) >= 2 and parts[-1].isdigit():
        level = int(parts[-1])

    return action, level


def AdminListRef(settings, threadId, level):
    if not isinstance(settings, dict):
        return []

    if level == 1:
        ga = settings.setdefault("groupAdmin", {})
        if not isinstance(ga, dict):
            settings["groupAdmin"] = {}
            ga = settings["groupAdmin"]
        lst = ga.setdefault(threadId, [])
        if not isinstance(lst, list):
            ga[threadId] = []
            lst = ga[threadId]
        return lst

    if level == 2:
        lst = settings.setdefault("adminBot", [])
        if not isinstance(lst, list):
            settings["adminBot"] = []
            lst = settings["adminBot"]
        return lst

    lst = settings.setdefault("highAdmin", [])
    if not isinstance(lst, list):
        settings["highAdmin"] = []
        lst = settings["highAdmin"]
    return lst


def addAdminPermission(this, message, data, userId, threadId, type):
    try:
        text = (getattr(message, "text", "") or "").strip()
        parts = text.split()

        settings = ReadServices(this.uid)
        if not isinstance(settings, dict):
            settings = {}

        uids = this.extractUids(data) or []

        if (len(parts) == 1 and not uids) or (len(parts) >= 2 and parts[1].lower() == "list"):
            owner, admins, hCount, bCount, gCount = BuildAdminList(this, settings, threadId)
            if SendAdminListImage(this, owner, admins, threadId, type, userId):
                return
            return SendAdminListText(this, admins, userId, threadId, type, hCount, bCount, gCount)

        action, level = ParseLevel(parts)
        if level is None or level not in (1, 2, 3):
            return this.sendMWarning("Invalid level", userId, threadId, type)

        if not uids:
            return this.sendMFailed("No target", userId, threadId, type)

        protectedUid = ""
        try:
            number = databaseReader().get("adminNumber")
            pn = this.fetchPhoneNumber(number)
            if isinstance(pn, dict):
                protectedUid = str(pn.get("uid") or "").strip()
            else:
                protectedUid = str(getattr(pn, "uid", "") or "").strip()
        except:
            pass

        levelName = {1: "Group admin", 2: "Bot admin", 3: "High admin"}[level]
        changed = False

        for uid in uids:
            uid = str(uid or "").strip()
            if not uid:
                continue

            admins = AdminListRef(settings, threadId, level)
            has = uid in admins
            name = this.userName(uid)

            if action == "add":
                if not has:
                    admins.append(uid)
                    changed = True
                msg = f"{levelName} {'Already added' if has else 'added'}: {name}"

            elif action == "remove":
                if protectedUid and uid == protectedUid:
                    return this.sendMWarning("You can't remove admin", userId, threadId, type)

                if has:
                    admins.remove(uid)
                    changed = True
                msg = f"{levelName} {'removed' if has else 'Not Found'}: {name}"

            else:
                if has:
                    admins.remove(uid)
                    msg = f"{levelName} removed: {name}"
                else:
                    admins.append(uid)
                    msg = f"{levelName} added: {name}"
                changed = True

            this.sendMSuccess(msg, userId, threadId, type)

        if changed:
            WriteService(this.uid, settings)

    except Exception as e:
        logger.errorMeta(e)


dependencies = {
    "name": "admin",
    "permission": 3,
    "cooldown": 3,
    "description": "Admin manage",
    "main": addAdminPermission
}