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

class MessageMongoModule(MongoModule):
    Key = "messageMongo"

    def _Collection(this, eng) -> str:
        cfg = eng.Cfg()
        return str((cfg.collections or {}).get("logger") or "loggerTable")

    def EnsureCommands(this, eng) -> List[Callable]:
        coll = this._Collection(eng)
        cmds = []
        
        def ensure_indexes(e):
            try:
                e.CreateIndex(coll, [("stamp", 1)])
                return True
            except:
                return False
        
        cmds.append(ensure_indexes)
        return cmds

    def GetCollection(this, eng) -> str:
        return this._Collection(eng)

    def BuildDoc(this, eng, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "kind": SafeStr(payload.get("kind")),
            "level_tag": SafeStr(payload.get("levelTag")),
            "stamp": SafeStr(payload.get("stamp")),
            "content": SafeStr(payload.get("content")),
            "meta": payload.get("meta") or {},
        }
