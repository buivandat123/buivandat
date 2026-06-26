# app/core/server/open.py
import app.core.server.tunnel as TunnelState
import subprocess, threading, os, json, re
from app.core.server.api import *
from modules.engine.data.data import databaseReader

tryUrlPattern = re.compile(r"(https?://[^\s|)]+)", re.I)
slugRe = re.compile(r"[^a-z0-9-]+")

def CleanUrl(url: str) -> str:
    return (url or "").strip().rstrip(".,;)]}")

def ExpandPath(p):
    return os.path.abspath(os.path.expanduser(p or ""))

def EnsureDir(path):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

def SlugHostLabel(s):
    s = (s or "").strip().lower()
    s = slugRe.sub("-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    if not s:
        return ""
    if len(s) > 63:
        s = s[:63].rstrip("-")
    return s

def JoinHost(label, zone):
    label = SlugHostLabel(label)
    zone = (zone or "").strip().strip(".").lower()
    if not label or not zone:
        return ""
    return f"{label}.{zone}"

def ReadServerPort(default=1000):
    p = globals().get("cfgPath")
    if isinstance(p, (str, bytes, os.PathLike)) and os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f) or {}
            return int(d.get("serverport", default))
        except:
            pass
    d = globals().get("cfgData")
    if isinstance(d, dict):
        try:
            return int(d.get("serverport", default))
        except:
            pass
    return int(default)

def ReadTunnelMode(default="cloudflared"):
    try:
        cfg = databaseReader() or {}
        mode = str(cfg.get("tunnel", default) or default).strip().lower()
        if mode == "nport":
            return "nport"
        if mode in ("cloudflared", "clf"):
            return "cloudflared"
    except:
        pass
    return "cloudflared"

def ReadServerName(default="app"):
    try:
        cfg = databaseReader() or {}
        v = cfg.get("serverName", default)
        v = (str(v).strip() if v is not None else default)
        return v or default
    except:
        return default

def ReadTunnelId(default=""):
    try:
        cfg = databaseReader() or {}
        v = cfg.get("tunnelId", default)
        v = (str(v).strip() if v is not None else default)
        return v or default
    except:
        return default

def ReadTunnelCreds(default=""):
    try:
        cfg = databaseReader() or {}
        v = cfg.get("tunnelCreds", default)
        v = (str(v).strip() if v is not None else default)
        return v or default
    except:
        return default

def ReadTunnelHost(default=""):
    try:
        cfg = databaseReader() or {}
        v = cfg.get("tunnelHost", default)
        v = (str(v).strip() if v is not None else default)
        return v or default
    except:
        return default

def ReadTunnelConfig(default="~/.cloudflared/config.yml"):
    try:
        cfg = databaseReader() or {}
        v = cfg.get("tunnelConfig", default)
        v = (str(v).strip() if v is not None else default)
        return v or default
    except:
        return default

def WriteCloudflaredConfig(configPath, tunnelId, credsPath, hostname, port):
    EnsureDir(configPath)
    hostname = (hostname or "").strip()
    lines = [
        f"tunnel: {tunnelId}",
        f"credentials-file: {credsPath}",
        "",
        "ingress:",
    ]
    if hostname:
        lines += [
            f"  - hostname: {hostname}",
            f"    service: http://127.0.0.1:{port}",
            "  - service: http_status:404",
        ]
    else:
        lines += [
            f"  - service: http://127.0.0.1:{port}",
            "  - service: http_status:404",
        ]
    tmp = configPath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, configPath)

def StartQuickCloudflared(*args, **kwargs):
    logger.base("⚠️ Cloudflared skipped - Termux")
    return None

def StartNamedCloudflared(port, cloudflaredPath="cloudflared", serviceName=None):
    cfg = databaseReader() or {}
    tunnelId = (str(cfg.get("tunnelId") or "").strip() or ReadTunnelId("").strip())
    if not tunnelId:
        return None

    credsPath = ExpandPath(str(cfg.get("tunnelCreds") or ReadTunnelCreds(f"~/.cloudflared/{tunnelId}.json")))
    if not os.path.exists(credsPath):
        return None

    zone = str(cfg.get("tunnelHost") or ReadTunnelHost("")).strip()
    if serviceName is None:
        serviceName = str(cfg.get("serverName") or ReadServerName("app")).strip() or "app"
    hostname = JoinHost(serviceName, zone)
    if not hostname:
        return None

    configPath = ExpandPath(str(cfg.get("tunnelConfig") or ReadTunnelConfig("~/.cloudflared/config.yml")))
    WriteCloudflaredConfig(configPath, tunnelId, credsPath, hostname, port)

    TunnelState.AppServerUrl = f"https://{hostname}"
    cmd = [cloudflaredPath, "tunnel", "--loglevel", "info", "--config", configPath, "run", tunnelId]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    TunnelState.TunnelProc = p

    def Reader():
        out = []
        ok = False
        try:
            for line in iter(p.stdout.readline, ""):
                out.append(line)
                s = line.lower()
                if "registered tunnel connection" in s:
                    ok = True
                    TunnelState.TunnelReady.set()
                    logger.base("Tunnel Manager Website OK")
                    logger.start(TunnelState.AppServerUrl)
                    break
                if "couldn't start tunnel" in s or "error=" in s:
                    break
        finally:
            if not ok:
                code = p.poll()
                if code is not None:
                    TunnelState.TunnelError = "".join(out[-200:]).strip()
                    TunnelState.TunnelReady.set()

    threading.Thread(target=Reader, daemon=True).start()
    return p

def StartTunnel(port=None, nportPath="nport", cloudflaredPath="cloudflared", serviceName=None):
    try:
        from app.core.server.server import EnsureFrontendBuild
        EnsureFrontendBuild(force=False)
    except:
        pass

    port = ReadServerPort(1000) if port is None else int(port)
    mode = ReadTunnelMode("cloudflared")
    if serviceName is None:
        serviceName = ReadServerName("app")

    TunnelState.AppServerUrl = None
    TunnelState.TunnelProc = None
    TunnelState.TunnelError = ""
    TunnelState.TunnelReady = threading.Event()

    if mode == "nport":
        serviceTag = f"{serviceName}-{port}" if serviceName else str(port)
        publicUrl = f"https://{serviceTag}.nport.link"
        cmd = [nportPath, str(port), "-s", serviceTag]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        TunnelState.TunnelProc = p
        TunnelState.AppServerUrl = publicUrl
        TunnelState.TunnelReady.set()
        logger.base("Tunnel Manager Website OK")
        logger.start(publicUrl)
        return p

    p = StartNamedCloudflared(port, cloudflaredPath, serviceName)
    if p:
        return p

    return StartQuickCloudflared(port, cloudflaredPath)

def WaitTunnel(*args, **kwargs):
    logger.base("⚠️ Tunnel skipped - Termux")
    return None
