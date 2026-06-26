# app/core/server/live/apiClient.py
from ..client import *
import re

@app.post("/api/account/update")
def AccountUpdate():
    try:
        account, _ = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    body = request.get_json(silent=True) or {}
    newUsername = body.get("username")
    newPassword = body.get("password")

    with Lock:
        bot, loginFile, path = AccountBot(account)
        if not bot:
            return Jsonfailed("Account not found", 404)

        if isinstance(newUsername, str) and newUsername.strip():
            bot["botAccount"] = newUsername.strip()

        if isinstance(newPassword, str) and newPassword.strip():
            bot["botPassword"] = newPassword.strip()

        try:
            _, meta = ReadJSONMeta(path)
            WriteBotANDMeta(path, bot, meta)
        except:
            pass

        if isinstance(newPassword, str) and newPassword.strip():
            session.clear()

        return jsonify({"ok": True, "updated": True, "file": loginFile, "relogin": bool(newPassword and str(newPassword).strip())})

@app.get("/api/logger/list")
def LoggerList():
    try:
        _, botIntId = AuthReq()
    except Exception as e:
        return Jsonfailed(str(e), 401)

    limit = min(max(int(request.args.get("limit", 50)), 1), 200)
    beforeId = request.args.get("beforeId")
    kind = str(request.args.get("kind", "message") or "message")
    q = str(request.args.get("q", "") or "")

    cfg = GetDbConfig(refresh=True)
    collectionName = str(((cfg.get("collections") or {}).get("logger") or "loggerTable")).strip()
    if not re.match(r"^[A-Za-z0-9_]+$", collectionName):
        collectionName = "loggerTable"

    client = DatabaseConfig(cfg)
    if not client:
        return Jsonfailed("DB connect fail", 500)

    try:
        baseDb = str(cfg.get("database", "main_data") or "main_data").strip() or "main_data"
        dbName = baseDb if baseDb.endswith(f"-{botIntId}") else f"{baseDb}-{botIntId}"
        db = client[dbName]
        collection = db[collectionName]

        query = {"kind": kind}
        query["meta.bot"] = str(botIntId)
        
        if beforeId:
            try:
                from bson.objectid import ObjectId
                query["_id"] = {"$lt": ObjectId(beforeId)}
            except:
                pass

        if q:
            query["content"] = {"$regex": q, "$options": "i"}

        cursor = collection.find(query).sort("_id", -1).limit(limit)
        docs = list(cursor)

        items = []
        for doc in docs:
            meta = doc.get("meta") or {}
            items.append({
                "id": str(doc.get("_id", "")),
                "kind": doc.get("kind", ""),
                "level": doc.get("level_tag") or "NOTICE",
                "bot": str(meta.get("bot") or botIntId),
                "prefix": meta.get("prefix") or "",
                "chat_type": meta.get("chat_type") or "",
                "group_name": meta.get("group_name") or "",
                "group_id": meta.get("group_id") or "",
                "user_name": meta.get("user_name") or "",
                "user_id": meta.get("user_id") or "",
                "msg_type": meta.get("msg_type") or "",
                "forward": meta.get("forward") or "",
                "ref": meta.get("ref") or "",
                "created_at": doc.get("stamp") or "",
                "content": doc.get("content") or "",
            })

    finally:
        try:
            client.close()
        except:
            pass

    nextBeforeId = str(items[-1]["id"]) if items else None
    return jsonify({"ok": True, "items": items, "nextBeforeId": nextBeforeId, "botIntId": str(botIntId), "collection": collectionName})
