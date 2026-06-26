# modules/login_hook.py
# -*- coding: utf-8 -*-
import os
import json
import time
from datetime import datetime

mainLogin = "asset/config/main_login.json"

def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        pass

def jsonLoader(filename):
    if not os.path.exists(filename):
        try:
            ensure_dir(os.path.dirname(filename))
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        except:
            pass
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def saveJson(filename, data):
    try:
        ensure_dir(os.path.dirname(filename))
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def loadBotManager():
    return jsonLoader("asset/config/bot-manager-database.json") or {}

def dataGroup(cfg):
    dg = cfg.get("dataGroup")
    if isinstance(dg, dict):
        return dg
    dg = {}
    cfg["dataGroup"] = dg
    return dg

def ReadLoginJson(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.loads(f.read() or "[]")
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            return data["data"]
        return []
    except:
        return []

def NormalizeBotItem(item):
    return item

def CheckBotExpiration(item):
    exp = item.get("expiredTime")
    if not exp:
        return True
    try:
        expiry = datetime.strptime(exp, "%H:%M:%S-%d/%m/%Y")
        if datetime.now() > expiry:
            item["status"] = False
            return False
        return True
    except:
        return True

def ExtractSessionCookies(item):
    sc = item.get("sessionCookies")
    if isinstance(sc, dict) and sc:
        return sc
    return {}

def LoadAllBotData():
    all_bots = []
    try:
        os.makedirs("asset/config/multibot", exist_ok=True)
    except:
        pass
    
    try:
        main_data = jsonLoader("asset/config/login.json")
        if "data" in main_data and isinstance(main_data["data"], list):
            for item in main_data["data"]:
                if isinstance(item, dict):
                    item["mainBot"] = True
                    item["filePath"] = "asset/config/login.json"
                    all_bots.append(item)
    except:
        pass
    
    try:
        account_dir = "asset/config/multibot"
        if os.path.exists(account_dir):
            for filename in os.listdir(account_dir):
                if filename.endswith("-login.json"):
                    account_file = os.path.join(account_dir, filename)
                    try:
                        account_data = ReadLoginJson(account_file)
                        for item in account_data:
                            if isinstance(item, dict):
                                item["mainBot"] = False
                                item["filePath"] = account_file
                                all_bots.append(item)
                    except:
                        pass
    except:
        pass
    
    return all_bots