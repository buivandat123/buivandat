# modules/services/hook/core_hook/extra_multibot_core.py
import os
import json
from datetime import datetime, timedelta

def GetOwnBot(client, uid=None, imei=None, username=None, botIntId=None):
    from modules.engine.data.data import jsonLoader
    data = jsonLoader("asset/config/login.json", {})
    for item in data.get("data", []):
        if item.get("botIntId") == str(client.uid) or item.get("imei") == str(client.imei):
            return item, "asset/config/login.json", data
    return None, None, None

def GetOwnBotByFilePath(client):
    from modules.engine.data.data import jsonLoader
    data = jsonLoader("asset/config/login.json", {})
    for item in data.get("data", []):
        if item.get("botIntId") == str(client.uid):
            return item, "asset/config/login.json", data
    return None, None, None

def ParseTimeExpression(expr):
    if not expr:
        return timedelta(days=30)
    total = timedelta(0)
    num = ""
    for char in expr:
        if char.isdigit():
            num += char
        elif char.lower() in "dhmsw":
            if num:
                val = int(num)
                if char.lower() == 'd':
                    total += timedelta(days=val)
                elif char.lower() == 'h':
                    total += timedelta(hours=val)
                elif char.lower() == 'm':
                    total += timedelta(minutes=val)
                elif char.lower() == 's':
                    total += timedelta(seconds=val)
                num = ""
    if total == timedelta(0):
        return timedelta(days=30)
    return total
