from ...index import *

class LoginAuth:
    def isLoggedIn(this):
        return this._state.isLoggedin()

    def getSession(this):
        return this._state.getCookies()

    def setSession(this, sessionCookies):
        try:
            d = this._cookiesToDict(sessionCookies)
            if not d:
                return False
            this._state.setCookies(d)
            this.uid = this._state.userClientId
            this._state._config["raw_cookies"] = this._cookiesToRaw(d)
            return True
        except Exception as e:
            print(f"setSession error: {e}")
            return False

    def getSecretKey(this):
        return this._state.getSecretkey()

    def setSecretKey(this, secretkey):
        try:
            this._state.setSecretkey(secretkey)
            return True
        except:
            return False

    def _tryParseJson(this, s):
        try:
            return json.loads(s)
        except:
            return None

    def _parseNetscape(this, text):
        out = {}
        for line in str(text or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#") and "\t" not in line:
                continue
            if line.startswith("#HttpOnly_"):
                line = line[len("#HttpOnly_"):]
            if "\t" not in line:
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            name = str(parts[5] or "").strip()
            value = str(parts[6] or "").strip()
            if name:
                out[name] = value
        return out

    def _cookiesToDict(this, cookies):
        if not cookies:
            return {}

        if isinstance(cookies, str):
            s = cookies.strip()
            if not s:
                return {}

            j = this._tryParseJson(s) if s[0] in "[{" and s[-1] in "]}" else None
            if j is not None:
                return this._cookiesToDict(j)

            if "Netscape HTTP Cookie File" in s or "\tTRUE\t" in s or "\tFALSE\t" in s:
                d = this._parseNetscape(s)
                if d:
                    return d

            out = {}
            for part in s.split(";"):
                part = part.strip()
                if not part or "=" not in part:
                    continue
                k, v = part.split("=", 1)
                k = k.strip()
                if k:
                    out[k] = v.strip()
            return out

        if isinstance(cookies, dict):
            for key in ("sessionCookies", "cookie", "raw_cookies", "rawCookies"):
                if key in cookies and cookies.get(key):
                    return this._cookiesToDict(cookies.get(key))

            lst = cookies.get("cookies")
            if isinstance(lst, list):
                out = {}
                for it in lst:
                    if not isinstance(it, dict):
                        continue
                    n = str(it.get("name") or "").strip()
                    v = it.get("value")
                    if n and v is not None:
                        out[n] = str(v)
                if out:
                    return out

            out = {}
            for k, v in cookies.items():
                k = str(k or "").strip()
                if not k or v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    out[k] = str(v)
            return out

        if isinstance(cookies, (list, tuple)):
            out = {}
            for it in cookies:
                d = this._cookiesToDict(it)
                if d:
                    out.update(d)
                    if "zpw_sek" in out:
                        return out
            return out

        return {}

    def _cookiesToRaw(this, cookies):
        d = this._cookiesToDict(cookies)
        if not d:
            if isinstance(cookies, str) and "=" in cookies:
                return cookies.strip()
            return ""
        return "; ".join(f"{k}={v}" for k, v in d.items())

    def GetSessionWsCookies(this):
        raw = ""
        try:
            raw = this._cookiesToRaw(this._state.getCookies())
        except:
            raw = ""
        if raw:
            return raw

        cfg = getattr(this._state, "_config", None) or {}
        for k in ("raw_cookies", "rawCookies", "cookies", "cookie", "sessionCookies"):
            raw = this._cookiesToRaw(cfg.get(k))
            if raw:
                return raw
        return ""

    def onLoggingIn(this, phone=None):
        pass

    def onLoggedIn(this, phone=None):
        pass