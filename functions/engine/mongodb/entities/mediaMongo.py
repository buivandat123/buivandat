from typing import Any, Dict, List, Optional, Callable

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

class MediaMongoModule(MongoModule):
    Key = "mediaMongo"

    def _Collection(this, eng) -> str:
        cfg = eng.Cfg()
        return str((cfg.collections or {}).get("mediaCache") or "mediaTable")

    def EnsureCommands(this, eng) -> List[Callable]:
        coll = this._Collection(eng)
        cmds = []
        
        def ensure_indexes(e):
            try:
                e.CreateIndex(coll, [("platform", 1), ("sid", 1)], unique=True)
                e.CreateIndex(coll, [("ts_ms", 1)])
                return True
            except:
                return False
        
        cmds.append(ensure_indexes)
        return cmds

    def GetCollection(this, eng) -> str:
        return this._Collection(eng)

    def BuildDoc(this, eng, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "platform": SafeStr(payload.get("platform")),
            "sid": SafeStr(payload.get("sid")),
            "file_url": "" if payload.get("file_url") is None else str(payload.get("file_url")),
            "meta": payload.get("meta") or {},
            "ts_ms": payload.get("ts_ms"),
        }
