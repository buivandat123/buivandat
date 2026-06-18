from dto.index import *

SpotifyApiBase = "https://api.spotify.com/v1"
SpotifyAuthUrl = "https://accounts.spotify.com/api/token"
CacheDir = "./assets/cache"
os.makedirs(CacheDir, exist_ok=True)

ClientId = "73d387c353224ebcab8125c67fb7f649"
ClientSecret = "562c513105f941528e17ba4d9ead31b4"
TimeoutSec = 10

AccessToken = None
TokenExpireAt = 0

def Norm(s):
    return (s or "").strip()

def GetToken():
    global AccessToken, TokenExpireAt
    now = int(time.time())
    if AccessToken and now < TokenExpireAt - 15:
        return AccessToken

    cid = Norm(ClientId)
    sec = Norm(ClientSecret)
    if not cid or not sec:
        raise RuntimeError("MissingSpotifyClientIdOrSecret")

    r = requests.post(
        SpotifyAuthUrl,
        data={"grant_type": "client_credentials"},
        auth=(cid, sec),
        timeout=TimeoutSec,
    )
    if r.status_code != 200:
        raise RuntimeError(f"SpotifyTokenError status={r.status_code} body={r.text}")

    j = r.json() or {}
    t = j.get("access_token")
    exp = int(j.get("expires_in") or 0)
    if not t or exp <= 0:
        raise RuntimeError(f"SpotifyTokenInvalid body={r.text}")

    AccessToken = t
    TokenExpireAt = now + exp
    return t

def H():
    return {"Authorization": f"Bearer {GetToken()}", "User-Agent": "Mozilla/5.0"}

def Get(path, params=None, retry=True):
    r = requests.get(
        f"{SpotifyApiBase}{path}",
        params=params or {},
        headers=H(),
        timeout=TimeoutSec,
    )
    if r.status_code == 401 and retry:
        global AccessToken, TokenExpireAt
        AccessToken = None
        TokenExpireAt = 0
        return Get(path, params=params, retry=False)
    if r.status_code != 200:
        raise RuntimeError(f"SpotifyApiError status={r.status_code} body={r.text}")
    return r.json()

def TrackIdFromLink(linkOrId):
    s = Norm(linkOrId)
    m = re.search(r"(?:spotify:track:|open\.spotify\.com/track/)([A-Za-z0-9]+)", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9]{10,}", s):
        return s
    return None

def PickCover(album):
    imgs = (album or {}).get("images") or []
    if not imgs:
        return None
    u = (imgs[0] or {}).get("url")
    return u or None

def TrackToSong(t):
    album = (t or {}).get("album") or {}
    artists = t.get("artists") or []
    artistName = ", ".join([a.get("name") for a in artists if a.get("name")]) or None
    return {
        "id": t.get("id"),
        "title": t.get("name"),
        "link": ((t.get("external_urls") or {}).get("spotify")),
        "artist": artistName,
        "cover": PickCover(album),
        "duration": int((t.get("duration_ms") or 0) // 1000),
        "like": int(t.get("popularity") or 0),
        "listen": 0,
        "comment": 0,
        "explicit": bool(t.get("explicit") or False),
        "previewUrl": t.get("preview_url"),
        "uri": t.get("uri"),
        "isPlayable": t.get("is_playable", None),
    }

def resolve(linkOrId, market="VN"):
    tid = TrackIdFromLink(linkOrId)
    if not tid:
        raise RuntimeError("InvalidSpotifyTrackLinkOrId")
    t = Get(f"/tracks/{tid}", params={"market": market})
    return TrackToSong(t)

def SearchSong(q, limit=10, market="VN", offset=0):
    r = Get(
        "/search",
        params={
            "q": q,
            "type": "track",
            "limit": int(limit),
            "offset": int(offset),
            "market": market,
        },
    )
    items = (((r or {}).get("tracks") or {}).get("items") or [])
    return [TrackToSong(t) for t in items]

def download(song):
    link = (song or {}).get("link")
    if not link:
        return None
    try:
        subprocess.run(["aio-down", link], capture_output=True, text=True, check=False)
    except:
        return None
    return None