from dto.index import *

def oauth():
    return OAuth1(
        "audiomack-web",
        "bd8a07e9f23fbe9d808646b730f89b8e",
        nonce="".join(random.choice(string.ascii_letters + string.digits) for _ in range(32)),
        timestamp=str(int(time.time())),
        signature_method="HMAC-SHA1",
    )

def extract_section(link):
    if not link or not isinstance(link, str):
        return None
    s = link
    if "://" in s:
        try:
            s = urlparse(s).path or s
        except Exception:
            s = link
    i = s.find("song/")
    if i == -1:
        return None
    return s[i + 5 :].lstrip("/")

def SearchSong(q):
    r = requests.get(
        "https://api.audiomack.com/v1/search",
        params={"q": q, "show": "songs", "limit": 10, "page": 1, "sort": "popular"},
        auth=oauth(),
        timeout=10,
    )
    r.raise_for_status()

    out = []
    for i in r.json().get("results", []):
        if i.get("type") == "song" and not i.get("geo_restricted"):
            link = (i.get("links") or {}).get("this")
            section = extract_section(link)
            out.append(
                {
                    "id": i.get("id"),
                    "title": i.get("title"),
                    "link": link,
                    "section": section,
                    "artist": i.get("artist"),
                    "thumb": i.get("image"),
                    "thumb2": (i.get("uploader") or {}).get("image"),
                    "duration": i.get("duration"),
                    "like": (i.get("stats") or {}).get("favorites-raw", 0),
                    "listen": (i.get("stats") or {}).get("plays-raw", 0),
                    "comment": (i.get("stats") or {}).get("comments", 0),
                }
            )
    return out

def download(song):
    song_id = song.get("id")
    if not song_id:
        return None

    section = song.get("section") or extract_section(song.get("link"))

    params = {"environment": "desktop-web", "hq": "true"}
    if section:
        params["section"] = section

    r = requests.get(
        f"https://api.audiomack.com/v1/music/play/{song_id}",
        params=params,
        auth=oauth(),
        timeout=15,
    )
    data = r.json() if r is not None else {}
    url = data.get("signedUrl")
    if not url:
        return None

    os.makedirs("./assets/cache", exist_ok=True)
    path = f"./assets/cache/{song_id}.mp3"

    with requests.get(url, stream=True, timeout=60) as rr, open(path, "wb") as f:
        rr.raise_for_status()
        for c in rr.iter_content(524288):
            if c:
                f.write(c)

    return path