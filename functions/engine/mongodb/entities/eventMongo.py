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

class EventMongoModule(MongoModule):
    Key = "eventMongo"

    def _Collection(this, eng) -> str:
        cfg = eng.Cfg()
        return str((cfg.collections or {}).get("event") or "eventTable")

    def EnsureCommands(this, eng) -> List[Callable]:
        coll = this._Collection(eng)
        cmds = []
        
        def ensure_indexes(e):
            try:
                e.CreateIndex(coll, [("stamp", 1)])
                e.CreateIndex(coll, [("event_type", 1)])
                return True
            except:
                return False
        
        cmds.append(ensure_indexes)
        return cmds

    def GetCollection(this, eng) -> str:
        return this._Collection(eng)

    def BuildDoc(this, eng, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event_type": SafeStr(payload.get("event_type")),
            "stamp": SafeStr(payload.get("stamp")),
            "raw": SafeStr(payload.get("raw")),
            "meta": payload.get("meta") or {},
            "json_text": SafeStr(payload.get("json")),
        }
