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

class UndoMongoModule(MongoModule):
    Key = "undoMongo"

    def _Collection(this, eng) -> str:
        cfg = eng.Cfg()
        return str((cfg.collections or {}).get("undo") or "undoTable")

    def EnsureCommands(this, eng) -> List[Callable]:
        coll = this._Collection(eng)
        cmds = []
        
        def ensure_indexes(e):
            try:
                e.CreateIndex(coll, [("cli_msg_id", 1)])
                e.CreateIndex(coll, [("msg_id", 1)])
                e.CreateIndex(coll, [("ts", 1)])
                e.CreateIndex(coll, [("bot_uid", 1), ("ts", 1)])
                e.CreateIndex(coll, [("bot_uid", 1), ("cli_msg_id", 1)])
                e.CreateIndex(coll, [("bot_uid", 1), ("msg_id", 1)])
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
            "msg_id": SafeStr(payload.get("msg_id")),
            "cli_msg_id": SafeStr(payload.get("cli_msg_id")),
            "uid_from": SafeStr(payload.get("uid_from")),
            "msg_type": SafeStr(payload.get("msg_type")),
            "content": payload.get("content") or {},
            "ts": payload.get("ts"),
        }
