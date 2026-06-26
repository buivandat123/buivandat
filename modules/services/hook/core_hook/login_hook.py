# modules/services/hook/core_hook/login_hook.py
import os
import json
import time
import threading
import random

mainLogin = "assets/config/login.json"

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

def ReadLoginJson(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def LoadAllBotData():
    all_bots = []
    try:
        data = jsonLoader(mainLogin, {})
        for item in data.get("data", []):
            if isinstance(item, dict):
                all_bots.append(item)
    except:
        pass
    
    multibot_dir = "asset/config/multibot"
    if os.path.exists(multibot_dir):
        for filename in os.listdir(multibot_dir):
            if filename.endswith("-login.json"):
                filepath = os.path.join(multibot_dir, filename)
                items = ReadLoginJson(filepath)
                for item in items:
                    if isinstance(item, dict):
                        item["filePath"] = filepath
                        all_bots.append(item)
    return all_bots

def NormalizeBotItem(item):
    if "status" not in item:
        item["status"] = False
    if "isActived" not in item:
        item["isActived"] = False
    if "mainBot" not in item:
        item["mainBot"] = False
    return item

def CheckBotExpiration(item):
    return True

def ExtractSessionCookies(item):
    try:
        cookies = item.get("sessionCookies")
        if isinstance(cookies, dict):
            return cookies
        if isinstance(cookies, str):
            return json.loads(cookies)
        return {}
    except:
        return {}

def SendMention(this, text, userId, threadId, type):
    this.sendMention(text, userId, threadId, type)

def GetUidFrom(data):
    return data.get("uid") or data.get("userId")

def GetMentionUid(this, data):
    mentions = data.get("mentions") or []
    if mentions and len(mentions) > 0:
        return mentions[0].get("uid") if isinstance(mentions[0], dict) else None
    return None

def IsMainBotUser(userId):
    return False

def SlugName(name):
    return name.replace(" ", "_").lower()

def ExtractJsonPayload(text):
    try:
        import json
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        return text
    except:
        return text

def BuildBotIndexList():
    bots = LoadAllBotData()
    result = []
    for bot in bots:
        if isinstance(bot, dict):
            result.append((bot, bot.get("filePath"), {}))
    return result

def GetBotByIndexOrMention(this, data, userId, threadId, type, token):
    bots = LoadAllBotData()
    if token and token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(bots):
            bot = bots[idx]
            return bot, bot.get("filePath"), []
    
    mention = GetMentionUid(this, data)
    if mention:
        for bot in bots:
            if str(bot.get("botIntId")) == str(mention):
                return bot, bot.get("filePath"), []
    
    return None, None, None

def GetOwnBot(this, data, userId, threadId, type):
    bots = LoadAllBotData()
    uid = GetUidFrom(data) or userId
    for bot in bots:
        if str(bot.get("botIntId")) == str(uid) or str(bot.get("clientBotId")) == str(uid):
            return bot, bot.get("filePath"), []
    return None, None, None

def GetOwnBotByFilePath(this):
    bots = LoadAllBotData()
    for bot in bots:
        if str(bot.get("botIntId")) == str(getattr(this, "uid", "")):
            return bot, bot.get("filePath"), []
    return None, None, None

def SaveBotField(filePath, items, bot, field, value):
    bot[field] = value
    if filePath == mainLogin:
        data = jsonLoader(mainLogin, {})
        for b in data.get("data", []):
            if b.get("botIntId") == bot.get("botIntId"):
                b[field] = value
        saveJson(mainLogin, data)
    else:
        saveJson(filePath, items)
    return True

def setGroupLink(this, threadId):
    return f"group_{threadId}"

def loadBotManager():
    return jsonLoader("asset/config/bot_manager.json", {})

def botManagerSave(cfg):
    return saveJson("asset/config/bot_manager.json", cfg)

def SessionHeader():
    return {"User-Agent": "Mozilla/5.0"}

def verifyClient(headers):
    return headers

def GenerateLoginQr(sessions):
    code = str(random.randint(100000, 999999))
    return code, sessions

def waiting_scan(code, sessions):
    time.sleep(2)
    return True

def waiting_confirm(code, sessions):
    return {"imei": "test_imei", "cookie": {}, "prefix": "!"}
