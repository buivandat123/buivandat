from ..client import *

def _PagePath(name):
    dist = os.path.join(PublicDir, "dist")
    target = os.path.join(dist, name)
    if os.path.isfile(target):
        return dist, name
    return PublicDir, name

def _LooksLikeAssetFile(p):
    
    
    return "." in os.path.basename(str(p or ""))

@app.get("/")
def Home():
    folder, page = _PagePath("dashboard.html" if session.get("account") else "login.html")
    return send_from_directory(folder, page)

@app.get("/dashboard")
def Dashboard():
    folder, page = _PagePath("dashboard.html" if session.get("account") else "login.html")
    return send_from_directory(folder, page)

@app.get("/<path:p>")
def StaticFiles(p):
    dist = os.path.join(PublicDir, "dist")
    fp_dist = os.path.join(dist, p)
    if os.path.isfile(fp_dist):
        return send_from_directory(dist, p)
    fp = os.path.join(PublicDir, p)
    if os.path.isfile(fp):
        return send_from_directory(PublicDir, p)
    if _LooksLikeAssetFile(p):
        return Jsonfailed("File not found", 404)
    folder, page = _PagePath("login.html")
    return send_from_directory(folder, page)
