import json
import os
import re
import threading
import time
from app.library.packages import *
from functions.engine.mongodb.settingMongo import getBotDatabase, readBotSetting, writeBotSetting
from threading import Lock
sf = 'Data'
luong = 10
sm = threading.Semaphore(luong)
file_lock = Lock()
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def projectPath(*parts):
    return os.path.join(PROJECT_ROOT, *parts)

def _normalizePath(path):
    p = str(path or "")
    if os.path.isabs(p):
        return p
    return projectPath(p)

def _storageRef(path):
    try:
        absPath = _normalizePath(path)
        rel = os.path.relpath(absPath, PROJECT_ROOT).replace("\\", "/")
        m = re.match(r"^assets/storage/([^/]+)/([^/]+)\.json$", rel)
        if not m:
            return None, None
        return str(m.group(1)), str(m.group(2))
    except:
        return None, None

def _mongoDb(uid):
    cfg = databaseReader() or {}
    return getBotDatabase(cfg, uid)

def _mongoReadJson(uid, key):
    cfg = databaseReader() or {}
    return readBotSetting(cfg, uid, str(key))

def _mongoWriteJson(uid, key, data):
    cfg = databaseReader() or {}
    return writeBotSetting(cfg, uid, data, str(key))

def ReadServices(uid):
    mongoData = _mongoReadJson(uid, "Setting")
    if isinstance(mongoData, dict):
        return mongoData
    data_file_path = projectPath("assets", "storage", str(uid), "Setting.json")
    try:
        with file_lock:
            with open(data_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        if isinstance(data, dict):
            _mongoWriteJson(uid, "Setting", data)
            return data
        _mongoWriteJson(uid, "Setting", {})
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        _mongoWriteJson(uid, "Setting", {})
        return {}

def WriteService(uid, settings):
    def write_task():
        try:
            ok = _mongoWriteJson(uid, "Setting", settings)
            if ok:
                return
            data_file_path = projectPath("assets", "storage", str(uid), "Setting.json")
            ensure_dir(os.path.dirname(data_file_path))
            with file_lock:
                with open(data_file_path, 'w', encoding='utf-8') as file:
                    json.dump(settings, file, ensure_ascii=False, indent=4)
        finally:
            sm.release()
    sm.acquire()
    thread = threading.Thread(target=write_task)
    thread.start()
    time.sleep(0.4)

def jsonLoader(path, default=None):
    uid, key = _storageRef(path)
    if uid and key:
        val = _mongoReadJson(uid, key)
        if val is not None:
            return val

    absPath = _normalizePath(path)
    if not os.path.exists(absPath):
        return default if default is not None else {}
    try:
        with open(absPath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if uid and key:
            _mongoWriteJson(uid, key, data)
        return data
    except Exception:
        return default if default is not None else {}
    
def databaseReader():
    db_config_path = projectPath("assets", "config", "database-config.json")
    try:
        with open(db_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def databaseWriter(config):
    db_config_path = projectPath("assets", "config", "database-config.json")
    ensure_dir(os.path.dirname(db_config_path))
    with open(db_config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def saveJson(path, data):
    uid, key = _storageRef(path)
    if uid and key:
        if _mongoWriteJson(uid, key, data):
            return
    absPath = _normalizePath(path)
    ensure_dir(os.path.dirname(absPath))
    with open(absPath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

class langWorker:
    _cache = None
    _tplCache = {}
    _kwCache = {}

    def load(this):
        if langWorker._cache is not None:
            return
        with open(projectPath("assets", "lang", "language.json"), "r", encoding="utf-8") as f:
            langWorker._cache = json.load(f) or {}
        langWorker._tplCache = {}
        langWorker._kwCache = {}

    def fmtThis(this, s):
        def repl(m):
            k = m.group(1)
            try:
                return str(getattr(this, k))
            except Exception:
                return m.group(0)
        return re.sub(r"\{this\.([A-Za-z_]\w*)\}", repl, str(s or ""))

    def buildTpl(this, langCode):
        cache = langWorker._cache or {}
        lang = cache.get(langCode)
        if not isinstance(lang, dict):
            lang = cache.get("vi") or {}
        if not isinstance(lang, dict):
            lang = {}

        items = []
        for src, dst in lang.items():
            if not isinstance(src, str) or not isinstance(dst, str):
                continue
            if "{" not in src or "}" not in src:
                continue

            parts = []
            i = 0
            keys = []
            ok = True

            while True:
                a = src.find("{", i)
                if a < 0:
                    parts.append(("lit", src[i:]))
                    break
                b = src.find("}", a + 1)
                if b < 0:
                    parts.append(("lit", src[i:]))
                    break

                parts.append(("lit", src[i:a]))
                name = src[a + 1:b].strip()
                if not name:
                    ok = False
                    break

                parts.append(("var", name))
                keys.append(name)
                i = b + 1

            if not ok:
                continue

            pat = ["^"]
            for t, v in parts:
                if t == "lit":
                    pat.append(re.escape(v))
                else:
                    pat.append("(.+?)")
            pat.append("$")

            try:
                rx = re.compile("".join(pat))
            except Exception:
                continue

            items.append((rx, dst, keys))

        langWorker._tplCache[langCode] = items
        return items

    def applyFmt(this, s, data):
        if not data:
            return str(s or "")

        def repl(m):
            k = (m.group(1) or "").strip()
            if k in data:
                return str(data.get(k))
            return m.group(0)

        return re.sub(r"\{([^{}]+)\}", repl, str(s or ""))

    def buildKeywords(this, langCode):
        cache = langWorker._cache or {}
        lang = cache.get(langCode) or cache.get("vi") or {}
        if not isinstance(lang, dict):
            lang = {}

        items = []
        for src, dst in lang.items():
            if not isinstance(src, str) or not isinstance(dst, str):
                continue
            s = src.strip()
            if not s or "{" in s or "}" in s:
                continue
            try:
                items.append((len(s), re.compile(re.escape(s), re.IGNORECASE), dst))
            except Exception:
                continue

        items.sort(key=lambda x: x[0], reverse=True)
        langWorker._kwCache[langCode] = items
        return items

    def applyKeywords(this, text, langCode):
        base = "" if text is None else str(text)
        if not base:
            return base

        items = langWorker._kwCache.get(langCode)
        if items is None:
            items = this.buildKeywords(langCode)

        out = base
        changed = False
        for _, rx, dst in items:
            if rx.search(out):
                out = rx.sub(dst, out)
                changed = True

        return this.fmtThis(out) if changed else base

    def t(this, key, langCode="vi"):
        this.load()
        langCode = (str(langCode or "vi")).strip() or "vi"
        key = "" if key is None else str(key)

        cache = langWorker._cache or {}
        lang = cache.get(langCode) or cache.get("vi") or {}
        if not isinstance(lang, dict):
            lang = {}

        out = lang.get(key)
        if out is not None:
            return this.fmtThis(out)

        items = langWorker._tplCache.get(langCode)
        if items is None:
            items = this.buildTpl(langCode)

        for rx, dst, keys in items:
            m = rx.match(key)
            if not m:
                continue

            vals = m.groups()
            fmt = {}
            for idx, n in enumerate(keys):
                if idx < len(vals):
                    fmt[n] = vals[idx]

            out = this.applyFmt(dst, fmt)
            return this.fmtThis(out)

        kw = this.applyKeywords(key, langCode)
        if kw != key:
            return kw

        return key
