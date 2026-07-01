# modules/engine/data/data.py
import os
import json
import time

def jsonLoader(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def saveJson(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def databaseReader():
    try:
        return jsonLoader("asset/config/database-config.json", {})
    except:
        return {}

def ReadServices(uid):
    path = f"assets/storage/{uid}/services.json"
    return jsonLoader(path, {})

def WriteService(uid, data):
    path = f"assets/storage/{uid}/services.json"
    return saveJson(path, data)

def dataGroup(cfg):
    return cfg.get("group", {})

def UpsertBotManagerRunning(uid, isMain, loginPath):
    pass

def saveConfigBot(name, uid, imei):
    pass
