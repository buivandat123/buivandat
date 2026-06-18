from functions.api.moderator import *
from functions.api import *
from functions.engine.data.data import databaseReader

def stripZwsp(s):
    return str(s or "").replace("\u200b", "")

class GroupHubInfo:
    def __init__(self, api, threadId, info):
        self.api = api
        self.threadId = str(threadId or "").strip()
        self.info = info
        self._link = None

    @property
    def name(self):
        return str(getattr(self.info, "name", None) or "Group không xác định")

    def member(self, memberName=""):
        try:
            tid = self.threadId
            if not tid:
                return []

            memList = getattr(self.info, "memVerList", None)
            if memList is None and isinstance(self.info, dict):
                memList = self.info.get("memVerList")
            memList = memList or []

            memList = [
                x[:-2] if isinstance(x, str) and x.endswith("_0") else x
                for x in memList
            ]

            r = self.api.getGroupMember(tid) or {}
            profiles = r.get("profiles") or {}

            q = [
                " ".join(x.strip().lower().split())
                for x in str(memberName or "").split(",")
                if x.strip()
            ]
            q = list(dict.fromkeys(q))

            rows = []
            seen = set()

            for uid in memList:
                uid = str(uid or "").strip()
                if not uid or uid in seen:
                    continue

                p = profiles.get(uid) or {}
                name = str(p.get("displayName") or p.get("zaloName") or uid).strip()

                if not q:
                    rows.append((uid, name))
                    seen.add(uid)
                    continue

                dn = " ".join(str(p.get("displayName") or "").lower().split())
                zn = " ".join(str(p.get("zaloName") or "").lower().split())

                if any(k in dn or k in zn for k in q):
                    rows.append((uid, name))
                    seen.add(uid)

            return rows
        except Exception as e:
            logger.errorMeta(f"member error {self.threadId}: {e}")
            return []

    @property
    def mod(self):
        adminIds = set(getattr(self.info, "adminIds", None) or [])
        creatorId = str(getattr(self.info, "creatorId", "") or "")
        return {"creator": creatorId, "admins": list(adminIds)}

    @property
    def vi(self):
        return "cộng đồng" if getattr(self.info, "type", 0) == 2 else "nhóm"

    @property
    def en(self):
        return "community" if getattr(self.info, "type", 0) == 2 else "group"

    @property
    def link(self):
        if self._link is not None:
            return self._link
        try:
            res = self.api.getGroupLink(self.threadId)
            if isinstance(res, dict):
                if res.get("errorcode", 0) != 0 or res.get("error_code", 0) != 0:
                    self._link = "Null"
                    return self._link
                self._link = str((res.get("data", {}) or {}).get("link") or "Null")
                self._link = stripZwsp(self._link) or "Null"
                return self._link
            self._link = "Null"
            return self._link
        except:
            self._link = "Null"
            return self._link

    @property
    def settings(self):
        return self.info.setting or {}

    def __str__(self):
        return self.en


class InfoFunctions:
    def groupHub(this, threadId):
        try:
            tid = str(threadId or "").strip()
            if not tid:
                return None
            raw = this.fetchGroupInfo(tid)
            grid = getattr(raw, "gridInfoMap", None)
            if not isinstance(grid, dict):
                return None
            info = grid.get(tid)
            if not info:
                return None
            return GroupHubInfo(this, tid, info)
        except:
            return None

    def userName(this, userId):
        try:
            uid = str(userId or "").strip()
            if not uid:
                return "Null"

            info = this.fetchUserInfo(uid)
            profiles = getattr(info, "changed_profiles", None)

            if isinstance(profiles, dict):
                p = profiles.get(uid)
                if isinstance(p, dict):
                    return str(p.get("zaloName") or "Null")
                return str(getattr(p, "zaloName", None) or "Null")

            return "Null"
        except Exception as e:
            logger.errorMeta(f"userName Lỗi khi lấy thông tin người dùng {userId}: {e}")
            return "Null"

    def getUserAvatar(this, uid):
        return (this.getAvatar(uid) or {}).get("bk_full_avatar")
    
    def getAdmin(this):
        adminNumber = databaseReader().get("adminNumber")
        if not adminNumber:
            logger.errorMeta("Admin number not set in database")
            return None
        return this.fetchPhoneNumber(adminNumber).get("uid")