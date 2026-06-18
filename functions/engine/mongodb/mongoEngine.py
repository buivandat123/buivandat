from dataclasses import dataclass, field
from typing import Any, Dict, Callable, Optional, List, Tuple
import threading, time, json
from functions.engine.mongodb.entities.agentMongo import AgentMemoryApi
from functions.engine.mongodb.entities import MessageMongoModule, EventMongoModule, MediaMongoModule, UndoMongoModule, AgentMemoryMongoModule

def SafeInt(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except:
        return default

def SafeStr(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v)
    return s if s != "" else None

@dataclass(frozen=True)
class DbConfig:
    host: str = "localhost"
    port: int = 27017
    user: str = ""
    password: str = ""
    database: str = ""
    authSource: str = "admin"
    connect_timeout: int = 5000
    server_selection_timeout: int = 5000
    collections: Dict[str, str] = field(default_factory=dict)
    create_db: bool = True

    @staticmethod
    def FromDict(d: Dict[str, Any]):
        colls = d.get("collections") or d.get("tableSQL") or {}
        return DbConfig(
            host=str(d.get("host", "localhost")),
            port=SafeInt(d.get("port", 27017), 27017),
            user=str(d.get("user", "")),
            password=str(d.get("password", "")),
            database=str(d.get("database", "")),
            authSource=str(d.get("authsource") or d.get("authSource", "admin")),
            connect_timeout=SafeInt(d.get("connect_timeout", 5000), 5000),
            server_selection_timeout=SafeInt(d.get("server_selection_timeout", 5000), 5000),
            collections=dict(colls),
            create_db=bool(d.get("create_db", True)),
        )

class MongoWorker:
    def __init__(
        this,
        pymongoCls,
        cfgProvider: Callable[[], DbConfig],
        pingSec: int = 30,
        maxQueue: int = 50000,
        logDebug: Optional[Callable[[str], None]] = None,
    ):
        this.MongoClient = pymongoCls
        this.cfgProvider = cfgProvider
        this.pingSec = int(pingSec or 30)
        this.maxQueue = int(maxQueue or 50000)
        this.logDebug = logDebug

        this.client = None
        this.db = None
        this.ready = False
        this.lastPing = 0.0

        this._q: List[Tuple[Optional[str], str, Dict[str, Any], Optional[str]]] = []
        this._cv = threading.Condition()
        this._stop = False
        this._th = None

        this._modules: Dict[str, Any] = {}
        this._ensured: Dict[str, bool] = {}

        this.messageMongo = _MessageApi(this)
        this.eventMongo = _EventApi(this)
        this.mediaMongo = _MediaApi(this)
        this.agentMemoryMongo = AgentMemoryApi(this)
        this.undoMongo = _UndoApi(this)

    def _Dbg(this, s: str):
        if this.logDebug:
            try:
                this.logDebug(s)
            except:
                pass

    def Start(this):
        if this._th:
            return
        this._stop = False
        this._th = threading.Thread(target=this._Loop, daemon=True)
        this._th.start()

    def Stop(this):
        with this._cv:
            this._stop = True
            this._cv.notify_all()

    def Cfg(this) -> DbConfig:
        return this.cfgProvider()

    def _IsOpen(this) -> bool:
        try:
            if this.client is None:
                return False
            this.client.server_info()
            return True
        except:
            return False

    def Connect(this) -> bool:
        cfg = this.Cfg()
        if not cfg.database:
            this.client = None
            this.db = None
            this.ready = False
            return False
        
        try:
            if cfg.user and cfg.password:
                uri = f"mongodb://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/?authSource={cfg.authSource}"
            else:
                uri = f"mongodb://{cfg.host}:{cfg.port}/"
            
            this.client = this.MongoClient(
                uri,
                serverSelectionTimeoutMS=cfg.server_selection_timeout,
                connectTimeoutMS=cfg.connect_timeout,
            )
            this.db = this.client[cfg.database]
            this.client.server_info()  # Test connection
            try:
                this.db["__meta"].update_one(
                    {"_id": "worker_init"},
                    {"$set": {"updatedAt": int(time.time())}},
                    upsert=True,
                )
            except:
                pass
            this.ready = True
            this.lastPing = time.time()
            return True
        except Exception as e:
            this.client = None
            this.db = None
            this.ready = False
            return False

    def EnsureConn(this) -> bool:
        if not this._IsOpen():
            return this.Connect()
        now = time.time()
        if now - this.lastPing >= this.pingSec:
            this.lastPing = now
            try:
                this.client.server_info()
            except:
                return this.Connect()
        return True

    def InsertOne(this, collection: str, doc: Dict[str, Any]) -> bool:
        if not collection or not doc:
            return False
        if not this.EnsureConn():
            return False
        try:
            this.db[collection].insert_one(doc)
            return True
        except:
            this.ready = False
            return False

    def FindOne(this, collection: str, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None):
        if not collection:
            return None
        if not this.EnsureConn():
            return None
        try:
            return this.db[collection].find_one(query, projection)
        except:
            this.ready = False
            return None

    def FindMany(this, collection: str, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None, limit: int = 0):
        if not collection:
            return []
        if not this.EnsureConn():
            return []
        try:
            cursor = this.db[collection].find(query, projection)
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except:
            this.ready = False
            return []

    def DeleteOne(this, collection: str, query: Dict[str, Any]) -> bool:
        if not collection:
            return False
        if not this.EnsureConn():
            return False
        try:
            result = this.db[collection].delete_one(query)
            return result.deleted_count > 0
        except:
            this.ready = False
            return False

    def CollectionExists(this, collection: str) -> bool:
        if not this.EnsureConn():
            return False
        try:
            return collection in this.db.list_collection_names()
        except:
            return False

    def CreateIndex(this, collection: str, keys: List[Tuple[str, int]], unique: bool = False) -> bool:
        if not collection or not keys:
            return False
        if not this.EnsureConn():
            return False
        try:
            this.db[collection].create_index(keys, unique=unique)
            return True
        except:
            return False

    def CountDocuments(this, collection: str, query: Dict[str, Any] = None) -> int:
        if not collection:
            return 0
        if not this.EnsureConn():
            return 0
        try:
            return this.db[collection].count_documents(query or {})
        except:
            return 0

    def DropCollection(this, collection: str) -> bool:
        if not collection:
            return False
        if not this.EnsureConn():
            return False
        try:
            this.db[collection].drop()
            return True
        except:
            return False

    def RegisterModule(this, mod: Any):
        k = str(getattr(mod, "Key", ""))
        if not k:
            return
        this._modules[k] = mod
        this._ensured.pop(k, None)
        try:
            this.EnsureSync(k)
        except:
            pass

    def _CollectionOf(this, key: str) -> Optional[str]:
        mod = this._modules.get(str(key))
        if not mod:
            return None
        fn = getattr(mod, "_Collection", None)
        if not callable(fn):
            return None
        try:
            return str(fn(this))
        except:
            return None

    def EnsureModule(this, key: str) -> bool:
        k = str(key)
        if this._ensured.get(k):
            return True
        mod = this._modules.get(k)
        if not mod:
            return False
        if not this.EnsureConn():
            return False
        ok = True
        for cmd in mod.EnsureCommands(this) or []:
            if cmd and not cmd(this):
                ok = False
        this._ensured[k] = bool(ok)
        return bool(ok)

    def EnsureSync(this, key: str) -> bool:
        return this.EnsureModule(key)

    def Push(this, key: Optional[str], collection: str, doc: Dict[str, Any], collName: Optional[str] = None):
        if not collection or not doc:
            return
        with this._cv:
            if len(this._q) >= this.maxQueue:
                this._q.pop(0)
            this._q.append((key, collection, doc, collName))
            this._cv.notify()

    def Flush(this, timeoutSec: float = 2.0) -> bool:
        end = time.time() + float(timeoutSec or 0)
        with this._cv:
            while this._q and time.time() < end:
                this._cv.wait(timeout=0.05)
            return not this._q

    def _Loop(this):
        while True:
            with this._cv:
                while not this._stop and not this._q:
                    this._cv.wait()
                if this._stop:
                    return
                key, collection, doc, collName = this._q.pop(0)
                this._cv.notify_all()

            if key and not this._ensured.get(str(key)):
                try:
                    this.EnsureSync(str(key))
                except:
                    pass

            ok = this.InsertOne(collection, doc)
            if ok and collName:
                this._Dbg(f"Mongo Engine Wrote To {collName}")

    def InsertModule(this, key: str, payload: Dict[str, Any]) -> bool:
        k = str(key)
        if not this._ensured.get(k):
            if not this.EnsureSync(k):
                return False
        mod = this._modules.get(k)
        if not mod:
            return False
        collection = mod.GetCollection(this)
        doc = mod.BuildDoc(this, payload)
        collName = this._CollectionOf(k)
        this.Push(k, collection, doc, collName=collName)
        return True

class _MessageApi:
    def __init__(this, eng: MongoWorker):
        this.eng = eng
        this.key = "messageMongo"

    def Write(this, kind: str, levelTag: str, stamp: str, content: str, meta: Optional[Dict[str, Any]] = None) -> bool:
        return this.eng.InsertModule(this.key, {"kind": kind, "levelTag": levelTag, "stamp": stamp, "content": content, "meta": meta or {}})

class _EventApi:
    def __init__(this, eng: MongoWorker):
        this.eng = eng
        this.key = "eventMongo"

    def Write(this, event_type: str, stamp: str, raw: str, meta: Optional[Dict[str, Any]] = None, jsonText: Optional[str] = None) -> bool:
        return this.eng.InsertModule(this.key, {"event_type": event_type, "stamp": stamp, "raw": raw, "json": jsonText, "meta": meta or {}})

class _MediaApi:
    def __init__(this, eng: MongoWorker):
        this.eng = eng
        this.key = "mediaMongo"

    def Write(this, platform: str, sid: str, file_url: str, meta: Optional[Dict[str, Any]] = None, ts_ms: Optional[int] = None) -> bool:
        if ts_ms is None:
            ts_ms = int(time.time() * 1000)
        return this.eng.InsertModule(this.key, {"platform": platform, "sid": sid, "file_url": file_url, "meta": meta or {}, "ts_ms": int(ts_ms)})

    def Get(this, platform: str, sid: str):
        cfg = this.eng.Cfg()
        coll = str((cfg.collections or {}).get("mediaCache") or "mediaTable")
        doc = this.eng.FindOne(coll, {"platform": SafeStr(platform), "sid": SafeStr(sid)})
        if not doc:
            return None
        meta = dict(doc.get("meta") or {})
        meta["fileUrl"] = doc.get("file_url")
        meta["timestamp"] = SafeInt(doc.get("ts_ms"), 0)
        return meta

    def Remove(this, platform: str, sid: str) -> bool:
        cfg = this.eng.Cfg()
        coll = str((cfg.collections or {}).get("mediaCache") or "mediaTable")
        return this.eng.DeleteOne(coll, {"platform": SafeStr(platform), "sid": SafeStr(sid)})

class _UndoApi:
    def __init__(this, eng: MongoWorker):
        this.eng = eng
        this.key = "undoMongo"
        this._last_check = 0.0

    def Write(this, bot_uid: str, msg_id: str, cli_msg_id: str, uid_from: str, msg_type: str, content, ts: Optional[int] = None) -> bool:
        if ts is None:
            ts = int(time.time())
        this._MaybeResetCollection()
        return this.eng.InsertModule(
            this.key,
            {
                "bot_uid": bot_uid,
                "msg_id": msg_id,
                "cli_msg_id": cli_msg_id,
                "uid_from": uid_from,
                "msg_type": msg_type,
                "content": content or {},
                "ts": int(ts),
            },
        )

    def _MaybeResetCollection(this):
        try:
            now = time.time()
            if now - this._last_check < 180:
                return
            this._last_check = now
        except:
            return
        cfg = this.eng.Cfg()
        coll = str((cfg.collections or {}).get("undo") or "undoTable")
        count = this.eng.CountDocuments(coll)
        if count < 1000:
            return
        try:
            this.eng.DropCollection(coll)
        except:
            return
        try:
            this.eng.EnsureSync(this.key)
        except:
            pass

    def _DocToItem(this, doc):
        if not doc:
            return None
        return {
            "msgId": str(doc.get("msg_id") or ""),
            "cliMsgId": str(doc.get("cli_msg_id") or ""),
            "uidFrom": str(doc.get("uid_from") or ""),
            "msgType": str(doc.get("msg_type") or ""),
            "content": doc.get("content") or {},
            "ts": SafeInt(doc.get("ts"), 0),
        }

    def GetByCli(this, bot_uid: str, cli_msg_id: str):
        if not cli_msg_id:
            return None
        cfg = this.eng.Cfg()
        coll = str((cfg.collections or {}).get("undo") or "undoTable")
        query = {"cli_msg_id": SafeStr(cli_msg_id)}
        if bot_uid:
            query["bot_uid"] = SafeStr(bot_uid)
        doc = None
        if this.eng.EnsureConn():
            try:
                doc = this.eng.db[coll].find_one(query, sort=[("_id", -1)])
            except:
                doc = None
        return this._DocToItem(doc)

    def GetByMsgId(this, bot_uid: str, msg_id: str):
        if not msg_id:
            return None
        cfg = this.eng.Cfg()
        coll = str((cfg.collections or {}).get("undo") or "undoTable")
        query = {"msg_id": SafeStr(msg_id)}
        if bot_uid:
            query["bot_uid"] = SafeStr(bot_uid)
        doc = None
        if this.eng.EnsureConn():
            try:
                doc = this.eng.db[coll].find_one(query, sort=[("_id", -1)])
            except:
                doc = None
        return this._DocToItem(doc)

def BuildMongoEng(MongoClientCls, cfgDict: Dict[str, Any], loggerDebug: Optional[Callable[[str], None]] = None) -> MongoWorker:
    cfg = DbConfig.FromDict(cfgDict)
    eng = MongoWorker(MongoClientCls, lambda: cfg, logDebug=loggerDebug)
    eng.Start()
    eng.Connect()
    eng.RegisterModule(MessageMongoModule())
    eng.RegisterModule(EventMongoModule())
    eng.RegisterModule(MediaMongoModule())
    eng.RegisterModule(AgentMemoryMongoModule())
    eng.RegisterModule(UndoMongoModule())
    return eng
