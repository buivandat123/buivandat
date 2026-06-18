# functions.py
# -*- coding: utf-8 -*-
import json
import os
import random
import time
import requests
from datetime import datetime

def jsonLoader(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def saveJson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def GetUidFrom(data):
    try:
        if hasattr(data, 'ownerId'):
            return str(data.ownerId)
    except:
        pass
    return None

def SendMention(client, text, userId, threadId, threadType):
    try:
        from zlapi.models import Message
        client.sendMessage(Message(text=text), thread_id=threadId, thread_type=threadType)
    except:
        pass

def GetAvatar(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(str(uid), {}).get('avatar', '')
    except:
        return ""

def ParseTimeExpression(expr):
    from datetime import timedelta
    expr = str(expr).lower()
    if 'h' in expr:
        return timedelta(hours=int(expr.replace('h', '')))
    if 'd' in expr:
        return timedelta(days=int(expr.replace('d', '')))
    if 'm' in expr:
        return timedelta(minutes=int(expr.replace('m', '')))
    return timedelta(hours=1)

def BuildBotIndexList():
    mainLogin = "assets/config/multibot/main.json"
    dataConfig = jsonLoader(mainLogin) or {}
    data = dataConfig.get("data", [])
    if not isinstance(data, list):
        return []
    result = []
    for i, bot in enumerate(data, 1):
        if isinstance(bot, dict):
            result.append((bot, f"{i}-login.json", None))
    return result

def restartABot(bot):
    pass

def shutdownABot(bot):
    pass

def GetOwnBot(client, data, userId, threadId, threadType):
    return None, None, None

def GetBotByIndexOrMention(client, data, userId, threadId, threadType, token):
    return None, None, None

def ExtractJsonPayload(text):
    try:
        return json.loads(text)
    except:
        return None

def IsMainBotUser(userId):
    return False

def GetMentionUid(this, data):
    return None

def logger():
    class Log:
        def errorMeta(self, msg):
            print(f"[ERROR] {msg}")
    return Log()

logger = logger()