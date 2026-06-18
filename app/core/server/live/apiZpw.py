from ..client import *

@app.get("/api/bot/getavatar")
def GetBotAvatar():
    try:
        _, botIntId = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)
    try:
        t = TargetGet(str(botIntId), False)
        if not t:
            return Jsonfailed("Bot not running", 404)
        ap = t.fetchAccountInfo()
        avatarUrl = ap.profile.get('avatar')
        return jsonify({"ok": True, "avatarUrl": avatarUrl})
    except Exception as e:
        return Jsonfailed(str(e), 500)
