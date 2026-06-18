from bot.system.evalExecutor import PrettyJson
from functions.services.artistcore.infoCard import CreateUserInfoCard
from dto.index import *

def timestampToDatetime(ts):
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts

def tsToVnDatetime(ts):
    try:
        if ts is None:
            return None
        v = int(ts)
        if v > 10_000_000_000:
            v = v / 1000
        tz = timezone(timedelta(hours=7))
        return datetime.fromtimestamp(v, tz).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts

def getUserInfo(this, message, data, userId, threadId, type):
    uids = this.extractUids(data) or []
    uid = uids[0] if uids else userId

    if not uid:
        return this.sendMWarning("Mention a user to get that info or not mention to get your own info", userId, threadId, type)

    try:
        info = this.fetchUserInfo(uid)
        profile = info.changed_profiles[uid]
        gender = {0: "Male", 1: "Female", 2: "Gay"}.get(profile.gender)
        mobile = {0: "No", 1: "Yes"}.get(profile.isActive)
        PC = {0: "No", 1: "Yes"}.get(profile.isActivePC)
        Web = {0: "No", 1: "Yes"}.get(profile.isActiveWeb)
        isbusiness = {0: "No", 1: "Yes"}.get(profile.bizPkg.get("pkgId", 0))
        avatar = this.getAvatar(uid).get("bk_full_avatar")
        cover = profile.cover
        avtAndCover = [avatar, cover]
        out = os.path.join(os.getcwd(), f"assets/cache/{timeNow}user_info_card.jpg")
        image = CreateUserInfoCard(out, profile)
        imageUrl = this.uploadImage(image, threadId, type)
        if imageUrl:
            imageUrls = imageUrl.get("hdUrl")
            with Image.open(image) as im:
                w, h = im.size
            this.sendImage(imageUrl=imageUrls, message=Message(text="", mention=Mention(userId, length=len("@Member"), offset=0)), threadId=threadId, type=type, width=w, height=h)
            os.remove(out)
        
        if ":debug" in data.content:
            this.sendMMessage(PrettyJson(profile), userId, threadId, type)
        if "text" in data.content:
            infoText = (f"""
Name: {profile.displayName}
Bio: {profile.status or "User has no bio"}

Gender: {gender}
Birthday: {profile.sdob or "Hidden"}
Number: {profile.phoneNumber or "Hidden"}
Last active: {timestampToDatetime(profile.lastActionTime) or "Hidden"}
Last update: {tsToVnDatetime(profile.lastUpdateTime) or "Hidden"}

Business: {isbusiness}
Mobile: {mobile}
PC: {PC}
Web: {Web}

Created account: {tsToVnDatetime(profile.createdTs) or "I Don't Know"}
""")
            this.sendMSuccess(infoText, userId, threadId, type)
            this.sendMultiImage(avtAndCover, threadId, type)
        return 
    except Exception as e:
        return this.sendMFailed(f"Failed to fetch user info\n\n{e}", userId, threadId, type)

dependencies = {
    "name": "info",
    "permission": 0,
    "description": "Get user info",
    "cooldown": 5,
    "main": getUserInfo
}