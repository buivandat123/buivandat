from dto.index import *
from functions.engine.mongodb.mongoEngine import MongoWorker, DbConfig
from functions.engine.mongodb.settingMongo import ensureBotDatabase, buildBotDatabaseName

MongoEng = None

def InitMongoWorker(this):
    e = getattr(this, "MongoWorker", None)
    if e:
        return e
    from functions.engine.mongodb.mongoEngine import BuildMongoEng
    from pymongo import MongoClient
    cfg = dict(databaseReader() or {})
    baseDb = str(cfg.get("database") or "main_data").strip() or "main_data"
    botUid = str(getattr(this, "uid", "") or "").strip()
    cfg["database"] = buildBotDatabaseName(baseDb, botUid)
    ensureBotDatabase(cfg, botUid)
    this.MongoWorker = BuildMongoEng(MongoClient, cfg, loggerDebug=None)
    return this.MongoWorker
