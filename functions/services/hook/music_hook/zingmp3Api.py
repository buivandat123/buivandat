from dto.index import *

URL = "https://zingmp3.vn"

VERSION = "1.0.00"
API_KEY = "88265e23d4284f25963e6eedac8fbfa3"
SECRET_KEY = "2aa2d1c561e809b267f3638c4a307aab"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": URL
})

_cookie = False

def hash256(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def hmac512(s, key):
    return hmac.new(
        key.encode("utf-8"),
        s.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()

def get_cookie(force=False):
    global _cookie
    if _cookie and not force:
        return
    session.get(URL, timeout=10)
    _cookie = True

def get_sig(path, param_str, ctime):
    raw = f"ctime={ctime}{param_str}version={VERSION}"
    return hmac512(path + hash256(raw), SECRET_KEY)

def zingmp3(path, extra=None):
    get_cookie()

    ctime = int(time.time())
    extra = extra or {}

    param_str = ""
    if "id" in extra:
        param_str = f"id={extra['id']}"

    sig = get_sig(path, param_str, ctime)

    params = {
        **extra,
        "ctime": ctime,
        "version": VERSION,
        "sig": sig,
        "apiKey": API_KEY
    }

    return session.get(
        f"{URL}{path}",
        params=params,
        timeout=10
    ).json()
def SearchSongv1(q, n=10):
    params = {
        "num": n,
        "query": q,
        "language": "vi",
        "ctime": int(time.time()),
        "version": "1.17.3",
        "apiKey": "X5BM3w8N7MKozC0B85o4KMlzLZKhV00y"
    }

    raw = "v1/web/ac-suggestions" + "".join(
        f"{k}={params[k]}" for k in sorted(params)
    )

    params["sig"] = hmac512(raw, params["apiKey"])

    return requests.get(
        "https://ac.zingmp3.vn/v1/web/ac-suggestions",
        params=params,
        timeout=10
    ).json()
chart_home = lambda: zingmp3("/api/v2/page/get/chart-home")
get_song    = lambda sid: zingmp3("/api/v2/song/get/info", {"id": sid})
get_stream  = lambda sid: zingmp3("/api/v2/song/get/streaming", {"id": sid})
get_lyric   = lambda sid: zingmp3("/api/v2/lyric/get/lyric", {"id": sid})
get_top100  = lambda: zingmp3("/api/v2/page/get/top-100")
get_playlist = lambda pid: zingmp3("/api/v2/page/get/playlist", {"id": pid})
SearchSongv2 = lambda q: zingmp3("/api/v2/search/multi", {"q": q})
