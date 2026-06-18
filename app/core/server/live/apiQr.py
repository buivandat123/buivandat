"""
QR Code Authentication API for bot registration.

Flow:
1. Frontend calls /api/qr/generate to get a QR image
2. Frontend polls /api/qr/status?code=xxx to check status
3. When confirmed, frontend submits phone via /api/qr/register-bot
4. Main bot receives notification and admin approves
"""

import base64
import hashlib
import io
import os
import time
import traceback
import uuid
import threading

from ..client import *

# In-memory QR sessions (code -> session_data)
# For production, use Redis or database
_qr_sessions: dict = {}
_qr_lock = threading.Lock()

# Session TTL in seconds
QR_EXPIRE_SECONDS = 180


def _cleanup_expired():
    """Remove expired QR sessions."""
    now = time.time()
    with _qr_lock:
        expired = [k for k, v in _qr_sessions.items() if now - v.get("created", 0) > QR_EXPIRE_SECONDS]
        for k in expired:
            del _qr_sessions[k]


def _generate_imei():
    """Generate a unique IMEI string for the bot."""
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    random_uuid = str(uuid.uuid4())
    md5_hash = hashlib.md5(user_agent.encode("utf-8")).hexdigest()
    return f"{random_uuid}-{md5_hash}"


try:
    import requests
    from PIL import Image
    HAS_QR_DEPS = True
except ImportError:
    HAS_QR_DEPS = False


def _create_zalo_session():
    """Create a session with Zalo headers."""
    if not HAS_QR_DEPS:
        return None
    sessions = requests.Session()
    header1 = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "origin": "https://chat.zalo.me",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "Accept-Encoding": "gzip",
        "referer": "https://chat.zalo.me/",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    }
    payload = {"continue": "https://chat.zalo.me/", "v": "5.5.7"}
    try:
        sessions.get("https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F", headers=header1, data=payload, timeout=10)
        sessions.post("https://id.zalo.me/account/logininfo", headers=header1, data=payload, timeout=10)
    except:
        pass
    return sessions


def _verify_client(sessions):
    """Verify device with Zalo."""
    if not sessions:
        return None
    veri_payload = {"type": "device", "continue": "https://zalo.me/pc", "v": "5.5.7"}
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    try:
        sessions.post("https://id.zalo.me/account/verify-client", headers=headers, data=veri_payload, timeout=10)
    except:
        pass
    return sessions


def _generate_qr(sessions):
    """Generate QR code from Zalo."""
    if not sessions or not HAS_QR_DEPS:
        return None, None, None
    payload = {"continue": "https://zalo.me/pc", "v": "5.5.7"}
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    try:
        response = sessions.post("https://id.zalo.me/account/authen/qr/generate", headers=headers, data=payload, timeout=15)
        data = response.json()
        qr_code = data.get("data", {}).get("image")
        token = data.get("data", {}).get("token")
        code = data.get("data", {}).get("code")
        if qr_code and code:
            return qr_code, code, sessions
    except Exception as e:
        traceback.print_exc()
    return None, None, None


def _waiting_scan(code, sessions):
    """Wait for QR scan (non-blocking check)."""
    if not sessions or not HAS_QR_DEPS:
        return None
    check_payload = {"code": code, "continue": "https://chat.zalo.me/", "v": "5.5.7"}
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    try:
        response = sessions.post("https://id.zalo.me/account/authen/qr/waiting-scan", headers=headers, data=check_payload, timeout=8)
        return response.json()
    except:
        return None


def _waiting_confirm(code, sessions):
    """Wait for QR confirm (non-blocking check)."""
    if not sessions or not HAS_QR_DEPS:
        return None
    confirm_payload = {
        "code": code,
        "gToken": "",
        "gAction": "CONFIRM_QR",
        "continue": "https://chat.zalo.me/index.html",
        "v": "5.5.7",
    }
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    try:
        response = sessions.post("https://id.zalo.me/account/authen/qr/waiting-confirm", headers=headers, data=confirm_payload, timeout=8)
        return response.json()
    except:
        return None


@app.get("/api/qr/generate")
def QrGenerate():
    """Generate a new QR code for login."""
    _cleanup_expired()

    if not HAS_QR_DEPS:
        return Jsonfailed("QR dependencies not installed (requests, PIL)", 500)

    try:
        # Create Zalo session and generate QR
        sessions = _create_zalo_session()
        sessions = _verify_client(sessions)
        qr_image, code, sessions = _generate_qr(sessions)

        if not qr_image or not code:
            return Jsonfailed("Failed to generate QR code from Zalo", 500)

        # Store session
        with _qr_lock:
            _qr_sessions[code] = {
                "created": time.time(),
                "status": "waiting",  # waiting -> scanned -> confirmed -> expired
                "sessions": sessions,
                "userId": None,
                "cookies": None,
                "imei": None,
            }

        return jsonify({"ok": True, "qrImage": qr_image, "code": code})


    except Exception as e:
        traceback.print_exc()
        return Jsonfailed(f"QR generation error: {e}", 500)


@app.get("/api/qr/status")
def QrStatus():
    """Check QR code status."""
    code = request.args.get("code", "").strip()
    if not code:
        return Jsonfailed("Missing code")

    _cleanup_expired()

    with _qr_lock:
        sess_data = _qr_sessions.get(code)
        if not sess_data:
            return jsonify({"ok": True, "status": "expired"})

    # Check if expired by time
    if time.time() - sess_data.get("created", 0) > QR_EXPIRE_SECONDS:
        with _qr_lock:
            if code in _qr_sessions:
                _qr_sessions[code]["status"] = "expired"
        return jsonify({"ok": True, "status": "expired"})

    current_status = sess_data.get("status", "waiting")
    if current_status in ("confirmed", "expired"):
        return jsonify({
            "ok": True,
            "status": current_status,
            "userId": sess_data.get("userId"),
            "cookies": sess_data.get("cookies"),
            "imei": sess_data.get("imei"),
        })

    # Poll Zalo for status
    sessions = sess_data.get("sessions")
    if not sessions:
        return jsonify({"ok": True, "status": "expired"})

    try:
        if current_status == "waiting":
            # Check if scanned
            scan_resp = _waiting_scan(code, sessions)
            if scan_resp and scan_resp.get("error_code") == 0:
                # Scanned! Move to confirm stage
                with _qr_lock:
                    if code in _qr_sessions:
                        _qr_sessions[code]["status"] = "scanned"
                return jsonify({"ok": True, "status": "scanned"})
            elif scan_resp and scan_resp.get("error_code") == -13:
                # Expired
                with _qr_lock:
                    if code in _qr_sessions:
                        _qr_sessions[code]["status"] = "expired"
                return jsonify({"ok": True, "status": "expired"})

        elif current_status == "scanned":
            # Check if confirmed
            confirm_resp = _waiting_confirm(code, sessions)
            if confirm_resp and confirm_resp.get("error_code") == 0:
                # Confirmed! Extract cookies
                imei = _generate_imei()
                cookies_dict = {}
                for cookie in sessions.cookies:
                    if cookie.name in ("zpw_sek", "zpsid", "_zlang", "__zi", "ozi"):
                        cookies_dict[cookie.name] = cookie.value

                with _qr_lock:
                    if code in _qr_sessions:
                        _qr_sessions[code]["status"] = "confirmed"
                        _qr_sessions[code]["cookies"] = cookies_dict
                        _qr_sessions[code]["imei"] = imei

                return jsonify({
                    "ok": True,
                    "status": "confirmed",
                    "cookies": cookies_dict,
                    "imei": imei,
                })
            elif confirm_resp and confirm_resp.get("error_code") == -13:
                with _qr_lock:
                    if code in _qr_sessions:
                        _qr_sessions[code]["status"] = "expired"
                return jsonify({"ok": True, "status": "expired"})

    except Exception as e:
        traceback.print_exc()

    return jsonify({"ok": True, "status": current_status})


@app.post("/api/qr/register-bot")
def QrRegisterBot():
    """
    Register a new bot after QR auth confirmed.
    This creates a pending bot entry for admin approval.
    """
    body = request.get_json(silent=True) or {}
    phone = str(body.get("phone", "")).strip()
    user_id = str(body.get("userId", "")).strip()
    cookies = body.get("cookies") or {}
    imei = str(body.get("imei", "")).strip()

    if not phone:
        return Jsonfailed("Missing phone number")
    if not cookies or not imei:
        return Jsonfailed("Missing session data")

    # At this point we have authenticated cookies from Zalo
    # We need to create a pending bot registration

    try:
        # Create pending bot entry
        pending_dir = os.path.join("assets", "config", "pending_bots")
        os.makedirs(pending_dir, exist_ok=True)

        pending_id = str(uuid.uuid4())[:8]
        pending_file = os.path.join(pending_dir, f"{pending_id}.json")

        pending_data = {
            "id": pending_id,
            "phone": phone,
            "imei": imei,
            "sessionCookies": cookies,
            "status": "pending",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)

        # Notify main bot (if available)
        try:
            from app.core.login import login as core_login
            gid = core_login.ResolveGroupId()
            mc = getattr(core_login, "mainclient", None)
            if gid and mc:
                msg = f"[BOT đăng ký mới]\nSĐT: {phone}\nID: {pending_id}\nDùng lệnh duyệt để kích hoạt bot này."
                mc.send(Message(text=msg), threadId=gid, type=ThreadType.GROUP)
        except:
            pass

        return jsonify({"ok": True, "pendingId": pending_id, "message": "Yêu cầu đã được gửi. Vui lòng chờ admin duyệt."})

    except Exception as e:
        traceback.print_exc()
        return Jsonfailed(f"Registration error: {e}", 500)
