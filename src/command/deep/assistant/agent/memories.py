from dto.index import *

def GetBotUid(this) -> str:
    return str(getattr(this, "uid", "") or "").strip()

def GetThreadKey(threadId: Any, data: Any) -> str:
    s = str(threadId or "").strip()
    if s:
        return s
    if isinstance(data, dict):
        v = data.get("groupId") or data.get("gid") or data.get("threadId")
    else:
        v = getattr(data, "groupId", None) or getattr(data, "gid", None) or getattr(data, "threadId", None)
    return str(v or "").strip()

def getMemoryText(this, threadId, data=None, limit: int = 12) -> str:
    eng = getattr(this, "MongoWorker", None)
    if not eng:
        return ""
    botUid = GetBotUid(this)
    threadKey = GetThreadKey(threadId, data)
    if not botUid or not threadKey:
        return ""
    return eng.agentMemoryMongo.GetText(botUid, threadKey, limit=int(limit or 12))

def getMemoryItems(this, threadId, data=None, limit: int = 50):
    eng = getattr(this, "MongoWorker", None)
    if not eng:
        return []
    botUid = GetBotUid(this)
    threadKey = GetThreadKey(threadId, data)
    if not botUid or not threadKey:
        return []
    return eng.agentMemoryMongo.GetItems(botUid, threadKey, limit=int(limit or 50))

def appendAgentMemory(this, threadId, data, userId: str, question: str, answer: str, limit: int = 200, meta: Optional[Dict[str, Any]] = None) -> bool:
    eng = getattr(this, "MongoWorker", None)
    if not eng:
        return False
    botUid = GetBotUid(this)
    threadKey = GetThreadKey(threadId, data)
    userId = str(userId or "").strip()
    if not botUid or not threadKey or not userId:
        return False

    ok = eng.agentMemoryMongo.Write(
        botUid,
        userId,
        threadKey,
        str(question or ""),
        str(answer or ""),
        meta=meta or {},
        ts=int(time.time()),
        limitKeep=int(limit or 200),
    )
    eng.Flush(1.5)
    return bool(ok)

def getLastMemory(this, threadId, data=None, offset: int = 0):
    eng = getattr(this, "MongoWorker", None)
    if not eng:
        return None
    botUid = GetBotUid(this)
    threadKey = GetThreadKey(threadId, data)
    if not botUid or not threadKey:
        return None
    return eng.agentMemoryMongo.GetLast(botUid, threadKey, offset=int(offset or 0))