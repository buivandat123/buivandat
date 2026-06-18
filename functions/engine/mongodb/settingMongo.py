import time
import threading
from typing import Any, Dict
from pymongo import MongoClient

_client_lock = threading.Lock()
_clients = {}

def _safe_str(v: Any, default: str = "") -> str:
    s = str(v if v is not None else default).strip()
    return s if s else default

def buildMongoUri(cfg: Dict[str, Any]) -> str:
    host = _safe_str(cfg.get("host"), "127.0.0.1")
    port = int(cfg.get("port") or 27017)
    user = _safe_str(cfg.get("user"), "")
    password = _safe_str(cfg.get("password"), "")
    authSource = _safe_str(cfg.get("authSource"), "admin")
    if user and password:
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource={authSource}"
    return f"mongodb://{host}:{port}/"

def buildBotDatabaseName(baseDatabase: str, botUid: Any) -> str:
    base = _safe_str(baseDatabase, "main_data")
    uid = _safe_str(botUid, "")
    if not uid:
        return base
    if base.endswith(f"-{uid}"):
        return base
    return f"{base}-{uid}"

def getMongoClient(cfg: Dict[str, Any]) -> MongoClient:
    uri = buildMongoUri(cfg)
    key = f"{uri}|{int(cfg.get('server_selection_timeout') or 5000)}|{int(cfg.get('connect_timeout') or 5000)}"
    with _client_lock:
        client = _clients.get(key)
        if client is None:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=int(cfg.get("server_selection_timeout") or 5000),
                connectTimeoutMS=int(cfg.get("connect_timeout") or 5000),
            )
            _clients[key] = client
    return client

def getBotDatabase(cfg: Dict[str, Any], botUid: Any):
    base = _safe_str(cfg.get("database"), "main_data")
    dbName = buildBotDatabaseName(base, botUid)
    c = getMongoClient(cfg)
    return c[dbName]

def ensureBotDatabase(cfg: Dict[str, Any], botUid: Any) -> bool:
    try:
        db = getBotDatabase(cfg, botUid)
        db["__meta"].update_one(
            {"_id": "db_init"},
            {"$set": {"createdAt": int(time.time()), "botUid": _safe_str(botUid, "")}},
            upsert=True,
        )
        return True
    except:
        return False

def readBotSetting(cfg: Dict[str, Any], botUid: Any, key: str = "Setting"):
    try:
        db = getBotDatabase(cfg, botUid)
        doc = db["jsonStore"].find_one({"_id": _safe_str(key, "Setting")})
        if not doc:
            return None
        return doc.get("data")
    except:
        return None

def writeBotSetting(cfg: Dict[str, Any], botUid: Any, data, key: str = "Setting") -> bool:
    try:
        db = getBotDatabase(cfg, botUid)
        db["jsonStore"].update_one(
            {"_id": _safe_str(key, "Setting")},
            {"$set": {"data": data, "updatedAt": int(time.time())}},
            upsert=True,
        )
        return True
    except:
        return False
