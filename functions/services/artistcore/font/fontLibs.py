from io import BytesIO
from pathlib import Path
import os
import hashlib
import requests
from PIL import ImageFont

class FontLib:
    BASE_RAW = "https://raw.githubusercontent.com/haonguyenbzzz-web/resource-libs/main"
    CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME") or (Path.home() / ".cache")) / "font-libs"

    @staticmethod
    def GetPath(filename):
        FontLib.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(str(filename).encode("utf-8")).hexdigest()[:16]
        out = FontLib.CACHE_DIR / f"{key}-{Path(str(filename)).name}"
        if out.exists() and out.stat().st_size > 0:
            return out
        if requests is None:
            return None
        url = f"{FontLib.BASE_RAW}/{filename}"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.content:
            return None
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_bytes(r.content)
        tmp.replace(out)
        return out

    @staticmethod
    def Load(filename, size):
        p = FontLib.GetPath(filename)
        if not p:
            return ImageFont.load_default()
        try:
            return ImageFont.truetype(str(p), int(size))
        except:
            return ImageFont.load_default()

class FaLib:
    CSS_URL = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
    TTF_URL = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.ttf"
    _map = None
    _ttfPath = None

    @staticmethod
    def _cachePath(name):
        FontLib.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(name.encode("utf-8")).hexdigest()[:16]
        return FontLib.CACHE_DIR / f"{key}-{name}"

    @staticmethod
    def _getBytes(url, outName, timeout=15):
        out = FaLib._cachePath(outName)
        if out.exists() and out.stat().st_size > 0:
            return out.read_bytes()
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.content:
            return None
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_bytes(r.content)
        tmp.replace(out)
        return r.content

    @staticmethod
    def _ensure():
        if FaLib._map is not None and FaLib._ttfPath is not None:
            return

        css = FaLib._getBytes(FaLib.CSS_URL, "fa4-font-awesome.min.css")
        if not css:
            FaLib._map = {}
        else:
            import re
            s = css.decode("utf-8", "ignore")
            m = {}
            for cls, code in re.findall(r"\.fa-([a-z0-9-]+):before\{content:\"\\([0-9a-f]{4})\"\}", s):
                m[cls] = chr(int(code, 16))
            FaLib._map = m

        ttf = FaLib._getBytes(FaLib.TTF_URL, "fa4-fontawesome-webfont.ttf")
        if ttf:
            FaLib._ttfPath = str(FaLib._cachePath("fa4-fontawesome-webfont.ttf"))
        else:
            FaLib._ttfPath = None

    @staticmethod
    def Font(size):
        FaLib._ensure()
        if not FaLib._ttfPath:
            return ImageFont.load_default()
        try:
            return ImageFont.truetype(FaLib._ttfPath, int(size))
        except:
            return ImageFont.load_default()

    @staticmethod
    def Glyph(name):
        FaLib._ensure()
        s = str(name or "").strip().lower()
        if s.startswith("fa "):
            s = s[3:].strip()
        if s.startswith("fa-"):
            s = s[3:]
        if s.startswith("fa_"):
            s = s[3:]
        return (FaLib._map or {}).get(s, "")