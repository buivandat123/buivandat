# app/core/server/server.py
import os
import json
import socket
import time
import threading
import logging
from flask import send_from_directory

from .libs import app, PublicDir
from .api import *

def _WebsiteDir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "website"))

def _FrontendDir() -> str:
    return os.path.join(_WebsiteDir(), "frontend")

def _DistDir() -> str:
    return os.path.join(_WebsiteDir(), "dist")

def _HasFrontendSource() -> bool:
    return os.path.isfile(os.path.join(_FrontendDir(), "package.json"))

def _HasFrontendDist() -> bool:
    dist = _DistDir()
    return (
        os.path.isfile(os.path.join(dist, "index.html")) and
        os.path.isfile(os.path.join(dist, "login.html")) and
        os.path.isfile(os.path.join(dist, "dashboard.html"))
    )

def EnsureFrontendBuild(force=False):
    if not _HasFrontendSource():
        return True
    if not force and _HasFrontendDist():
        return True
    return True

def _ConfigPath() -> str:
    return os.path.join("assets", "config", "database-config.json")

def _ConfigData() -> dict:
    path = _ConfigPath()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def SavePort(p: int):
    path = _ConfigPath()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}
    data["serverport"] = p
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def IsPortFree(p: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", p))
        return True
    except OSError:
        return False
    finally:
        s.close()

def Run():
    cfg = _ConfigData()
    p = int(cfg.get("serverport", 5000))
    while not IsPortFree(p):
        p += 1
    if p != cfg.get("serverport"):
        SavePort(p)
    
    print(f"\n✅ Server đang chạy tại: http://localhost:{p}")
    print(f"🔐 Admin: /admin/login (pass: admin123)")
    print(f"🤖 Bot: /bot/<id>/login")
    print("Press Ctrl+C to stop\n")
    
    app.run(host="0.0.0.0", port=p, debug=False, use_reloader=False)
    return p

def Open():
    EnsureFrontendBuild(force=False)
    threading.Thread(target=Run, daemon=True).start()
    port = int(_ConfigData().get("serverport", 5000))
    time.sleep(0.7)
    print(f"[Server] Port {port} OK")
