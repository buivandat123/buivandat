# app/core/login.py
# -*- coding: utf-8 -*-
import os
import json

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

def get_all_bots():
    data = jsonLoader("asset/config/login.json") or {}
    return data.get("data", [])

def get_bot_by_account(account):
    bots = get_all_bots()
    for bot in bots:
        if str(bot.get("botAccount")) == str(account):
            return bot
    return None

def get_bot_by_id(bot_id):
    bots = get_all_bots()
    for bot in bots:
        if str(bot.get("botIntId")) == str(bot_id):
            return bot
    return None

def save_bot(bot):
    try:
        data = jsonLoader("asset/config/login.json") or {}
        bots = data.get("data", [])
        found = False
        for i, b in enumerate(bots):
            if str(b.get("botIntId")) == str(bot.get("botIntId")):
                bots[i] = bot
                found = True
                break
        if not found:
            bots.append(bot)
        data["data"] = bots
        
        # Đồng bộ dataBot
        if "dataBot" not in data:
            data["dataBot"] = {}
        data["dataBot"][str(bot.get("botIntId"))] = bot.get("filePath", "")
        
        saveJson("asset/config/login.json", data)
        return True
    except Exception as e:
        print(f"[Login] Save bot error: {e}")
        return False

def delete_bot(bot_id):
    try:
        data = jsonLoader("asset/config/login.json") or {}
        bots = data.get("data", [])
        data["data"] = [b for b in bots if str(b.get("botIntId")) != str(bot_id)]
        if "dataBot" in data:
            data["dataBot"].pop(str(bot_id), None)
        saveJson("asset/config/login.json", data)
        return True
    except:
        return False
