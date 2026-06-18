from app.core.server.api import *
import logging
import subprocess

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
    try:
#         subprocess.run(["npm", "run", "build"], cwd=_WebsiteDir(), check=True)  # Skipped for Termux
        return True
    except Exception as e:
        print(f"[web] frontend build failed: {e}")
        return False

def _ConfigPath() -> str:
    p = globals().get("cfgPath")
    if isinstance(p, (str, bytes, os.PathLike)):
        return str(p)
    return os.path.join("assets", "config", "database-config.json")

def _ConfigData() -> dict:
    d = globals().get("cfgData")
    return d if isinstance(d, dict) else {}

def SavePort(p: int):
    path = _ConfigPath()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = _ConfigData().copy()
    data["serverport"] = p
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    globals()["cfgData"] = data

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
    p = int(cfg.get("serverport", 1000))
    while not IsPortFree(p):
        p += 1
    if p != cfg.get("serverport"):
        SavePort(p)
        

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    log.disabled = True
    
    app.logger.disabled = True
    app.config["ENV"] = "production"
    app.config["DEBUG"] = False

    app.run(host="0.0.0.0", port=p, debug=False, use_reloader=False)
    return p

def Open():
    EnsureFrontendBuild(force=False)
    threading.Thread(target=Run, daemon=True).start()
    port = int(_ConfigData().get("serverport", 1000))
    time.sleep(0.7)
    logger.base(f"Server {port} OK")
