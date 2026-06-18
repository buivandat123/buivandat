from typing import Any, Dict, List, Optional, Callable
import json, time

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

class MongoModule:
    Key: str = ""
    def EnsureCommands(this, eng) -> List[Callable]:
        return []
    def GetCollection(this, eng) -> str:
        return ""
    def BuildDoc(this, eng, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    def _Collection(this, eng) -> str:
        return ""

class AgentMemoryMongoModule(MongoModule):
    Key = "agentMemoryMongo"

    def _Collection(this, eng) -> str:
        cfg = eng.Cfg()
        return str((cfg.collections or {}).get("agentMemory") or "agentMemoryTable")

    def EnsureCommands(this, eng) -> List[Callable]:
        coll = this._Collection(eng)
        cmds = []
        
        def ensure_indexes(e):
            try:
                e.CreateIndex(coll, [("bot_uid", 1), ("thread_id", 1), ("_id", 1)])
                e.CreateIndex(coll, [("bot_uid", 1), ("thread_id", 1), ("ts", 1)])
                e.CreateIndex(coll, [("uid_from", 1), ("ts", 1)])
                return True
            except:
                return False
        
        cmds.append(ensure_indexes)
        return cmds

    def GetCollection(this, eng) -> str:
        return this._Collection(eng)

    def BuildDoc(this, eng, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "bot_uid": SafeStr(payload.get("bot_uid")),
            "uid_from": SafeStr(payload.get("uid_from")),
            "thread_id": SafeStr(payload.get("thread_id")),
            "q": SafeStr(payload.get("q")),
            "a": SafeStr(payload.get("a")),
            "meta": payload.get("meta") or {},
            "ts": SafeInt(payload.get("ts"), 0),
        }

class AgentMemoryApi:
    def __init__(this, eng):
        this.eng = eng
        this.key = "agentMemoryMongo"
        this._last_trim = 0.0

    def _Collection(this) -> str:
        cfg = this.eng.Cfg()
        return str((cfg.collections or {}).get("agentMemory") or "agentMemoryTable")

    def Write(this, bot_uid: str, uid_from: str, thread_id: str, q: str, a: str, meta: Optional[Dict[str, Any]] = None, ts: Optional[int] = None, limitKeep: int = 200) -> bool:
        if ts is None:
            ts = int(time.time())
        this._MaybeTrim(bot_uid, thread_id, SafeInt(limitKeep, 200))
        return this.eng.InsertModule(
            this.key,
            {
                "bot_uid": bot_uid,
                "uid_from": uid_from,
                "thread_id": thread_id,
                "q": q,
                "a": a,
                "meta": meta or {},
                "ts": int(ts),
            },
        )

    def GetText(this, bot_uid: str, thread_id: str, limit: int = 12) -> str:
        lim = max(1, SafeInt(limit, 12))
        coll = this._Collection()
        docs = []
        if this.eng.EnsureConn():
            try:
                docs = list(
                    this.eng.db[coll]
                    .find({"bot_uid": SafeStr(bot_uid), "thread_id": SafeStr(thread_id)}, {"q": 1, "a": 1, "_id": 0})
                    .sort("_id", -1)
                    .limit(lim)
                )
                docs.reverse()
            except:
                docs = []
        
        if not docs:
            return ""

        out: List[str] = []
        for doc in docs:
            q = (doc.get("q") or "").strip()
            a = (doc.get("a") or "").strip()
            if q or a:
                out.append(f"- User: {q}\n  Agent: {a}")
        return "\n".join(out)

    def GetItems(this, bot_uid: str, thread_id: str, limit: int = 50):
        lim = max(1, SafeInt(limit, 50))
        coll = this._Collection()
        docs = []
        if this.eng.EnsureConn():
            try:
                docs = list(
                    this.eng.db[coll]
                    .find({"bot_uid": SafeStr(bot_uid), "thread_id": SafeStr(thread_id)}, {"q": 1, "a": 1, "ts": 1, "_id": 0})
                    .sort("_id", -1)
                    .limit(lim)
                )
                docs.reverse()
            except:
                docs = []

        out = []
        for doc in docs:
            out.append({"q": doc.get("q") or "", "a": doc.get("a") or "", "ts": SafeInt(doc.get("ts"), 0)})
        return out

    def GetLast(this, bot_uid: str, thread_id: str, offset: int = 0):
        off = max(0, SafeInt(offset, 0))
        coll = this._Collection()
        doc = None
        if this.eng.EnsureConn():
            try:
                docs = list(
                    this.eng.db[coll]
                    .find({"bot_uid": SafeStr(bot_uid), "thread_id": SafeStr(thread_id)}, {"q": 1, "a": 1, "ts": 1, "_id": 0})
                    .sort("_id", -1)
                    .skip(off)
                    .limit(1)
                )
                doc = docs[0] if docs else None
            except:
                doc = None

        if not doc:
            return None
        return {"q": doc.get("q") or "", "a": doc.get("a") or "", "ts": SafeInt(doc.get("ts"), 0)}

    def Clear(this, bot_uid: str, thread_id: str) -> bool:
        coll = this._Collection()
        if not this.eng.EnsureConn():
            return False
        try:
            result = this.eng.db[coll].delete_many({"bot_uid": SafeStr(bot_uid), "thread_id": SafeStr(thread_id)})
            return result.deleted_count > 0
        except:
            return False

    def _MaybeTrim(this, bot_uid: str, thread_id: str, keep: int):
        try:
            now = time.time()
            if now - this._last_trim < 30:
                return
            this._last_trim = now
        except:
            return
        if keep < 50:
            keep = 50
        
        coll = this._Collection()
        
        if not this.eng.EnsureConn():
            return
        
        try:
            # Count total documents
            count = this.eng.CountDocuments(coll, {"bot_uid": SafeStr(bot_uid), "thread_id": SafeStr(thread_id)})
            
            if count <= keep:
                return
            
            # Get IDs to keep (latest ones)
            docs_to_keep = list(
                this.eng.db[coll]
                .find({"bot_uid": SafeStr(bot_uid), "thread_id": SafeStr(thread_id)}, {"_id": 1})
                .sort("_id", -1)
                .limit(keep)
            )
            
            keep_ids = [doc["_id"] for doc in docs_to_keep]
            
            # Delete documents not in keep list
            this.eng.db[coll].delete_many({
                "bot_uid": SafeStr(bot_uid),
                "thread_id": SafeStr(thread_id),
                "_id": {"$nin": keep_ids}
            })
        except:
            pass
