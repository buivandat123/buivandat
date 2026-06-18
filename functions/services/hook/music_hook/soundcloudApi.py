from dto.index import *

BASE_API = "https://api-v2.soundcloud.com"
BASE_WEB = "https://soundcloud.com"
CACHE_DIR = "./assets/cache"
os.makedirs(CACHE_DIR, exist_ok=True)
_client_id = None

def _h():
    return {"User-Agent": "Mozilla/5.0",'Authorization': 'OAuth 2-304104-1536374940-zbkU5uUKw1B9H',"Referer": BASE_WEB}

def _cid_ok(cid):
    try:
        return requests.get(f"{BASE_API}/search/tracks", params={"q": "test", "client_id": cid, "limit": 1}, headers=_h(), timeout=5).status_code == 200
    except:
        return False

def _cid():
    global _client_id
    if _client_id:
        return _client_id
    fb = "vjvE4M9RytEg9W09NH1ge2VyrZPUSKo5"
    if _cid_ok(fb):
        _client_id = fb
        return fb
    s = requests.get(BASE_WEB, headers=_h(), timeout=10).text
    for t in BeautifulSoup(s, "html.parser").find_all("script", crossorigin=True)[::-1]:
        src = t.get("src")
        if not src:
            continue
        m = re.search(r'client_id:"(.*?)"', requests.get(src, headers=_h(), timeout=10).text)
        if m:
            _client_id = m.group(1)
            return _client_id
    raise RuntimeError

def _resolve(link):
    return requests.get(f"{BASE_API}/resolve", params={"url": link, "client_id": _cid()}, headers=_h(), timeout=10).json()

def SearchSong(q, limit=10):
    r = requests.get(
        f"{BASE_API}/search/tracks",
        params={"q": q, "client_id": _cid(), "limit": limit},
        headers=_h(),
        timeout=10
    ).json()

    return [{
        "id": t["id"],
        "title": t["title"],
        "link": t["permalink_url"],
        "artist": t["user"]["username"],
        "cover": (
            (t.get("artwork_url") or "").replace("-large", "-t500x500")
            or (t["user"].get("avatar_url") or "").replace("-large", "-t500x500")
            or None
        ),

        "duration": t.get("duration", 0) // 1000,
        "like": t.get("likes_count", 0),
        "listen": t.get("playback_count", 0),
        "comment": t.get("comment_count", 0),
    } for t in r.get("collection", [])]

def download(song):
    for t in _resolve(song["link"]).get("media", {}).get("transcodings", []):
        if t["format"]["protocol"] == "progressive":
            u = requests.get(t["url"], params={"client_id": _cid()}, headers=_h(), timeout=10).json().get("url")
            if not u:
                return None
            fn = re.sub(r'[<>:"/\\|?*]', "_", f"{song['id']}_{song['title']}") + ".mp3"
            p = os.path.join(CACHE_DIR, fn)
            with requests.get(u, stream=True, timeout=30) as r, open(p, "wb") as f:
                for c in r.iter_content(524288):
                    f.write(c)
            return p
    return None