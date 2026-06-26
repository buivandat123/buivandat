# app/core/server/live/apiQr.py
from ..client import *
import uuid
import hashlib
import time

qr_sessions = {}

@app.get("/api/qr/generate")
def QrGenerate():
    try:
        code = str(uuid.uuid4())[:8]
        qr_sessions[code] = {
            "created": time.time(),
            "status": "waiting"
        }
        return jsonify({"ok": True, "qrImage": "", "code": code})
    except Exception as e:
        return Jsonfailed(str(e), 500)

@app.get("/api/qr/status")
def QrStatus():
    code = request.args.get("code", "").strip()
    if not code:
        return Jsonfailed("Missing code")
    
    sess = qr_sessions.get(code)
    if not sess:
        return jsonify({"ok": True, "status": "expired"})
    
    return jsonify({"ok": True, "status": sess.get("status", "waiting")})

@app.post("/api/qr/register-bot")
def QrRegisterBot():
    body = request.get_json(silent=True) or {}
    phone = str(body.get("phone", "")).strip()
    cookies = body.get("cookies") or {}
    imei = str(body.get("imei", "")).strip()
    
    if not phone:
        return Jsonfailed("Missing phone number")
    
    return jsonify({"ok": True, "pendingId": str(uuid.uuid4())[:8], "message": "Yêu cầu đã được gửi"})
