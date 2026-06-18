# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETING_FILE = os.path.join(BASE_DIR, "asset", "seting.json")

def load_settings():
    try:
        with open(SETING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"admin": "", "adm": []}

def get_owner():
    settings = load_settings()
    return str(settings.get("admin", ""))

def get_admins():
    settings = load_settings()
    admins = settings.get("adm", [])
    return set(str(x) for x in admins)

def is_owner(author_id):
    return str(author_id) == get_owner()

def is_admin(author_id):
    if is_owner(author_id):
        return True
    return str(author_id) in get_admins()