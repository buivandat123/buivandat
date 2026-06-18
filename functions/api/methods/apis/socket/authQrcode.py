import requests
import time
import json
import base64
from PIL import Image
import io
import traceback
import uuid
import hashlib
import os
import tempfile
import qrcode
from PIL import Image

def imeiGenerate():
    userAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    random_uuid = str(uuid.uuid4())
    md5_hash = hashlib.md5(userAgent.encode("utf-8")).hexdigest() 
    zalo_uuid = f"{random_uuid}-{md5_hash}"
    return zalo_uuid

def SessionHeader():
    sessions = requests.Session()
    header1 = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "sec-ch-ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Linux\"",
        "origin": "https://chat.zalo.me",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "Accept-Encoding": "gzip",
        "referer": "https://chat.zalo.me/",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    }
    payload = {
        "continue": "https://chat.zalo.me/",
        "v": "5.5.7"
    }
    sessions.get(
        "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        headers=header1,
        data=payload
    )
    sessions.post(
        "https://id.zalo.me/account/logininfo",
        headers=header1,
        data=payload
    )
    return sessions


def verifyClient(sessions):
    veri_payload = {
        "type": "device",
        "continue": "https://zalo.me/pc",
        "v": "5.5.7"
    }
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    sessions.post(
        "https://id.zalo.me/account/verify-client",
        headers=headers,
        data=veri_payload
    )
    return sessions


def GetZaloRes(sessions):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "upgrade-insecure-requests": "1",
        "Referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    try:
        cookies = sessions.cookies
        response = sessions.get(
            "https://id.zalo.me/account/checksession?continue=https%3A%2F%2Fchat.zalo.me%2Findex.html",
            headers=headers,
            cookies=cookies,
        )
        return response
    except Exception as e:
        print(f"Lỗi khi kiểm tra session: {e}")
        traceback.print_exc()
        return None

def fetchUserinfoQR(sessions):
    headers = {
        "accept": "*/*",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Referer": "https://chat.zalo.me/",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    try:
        response = sessions.get(
            "https://jr.chat.zalo.me/jr/userinfo",
            headers=headers
        )
        return response.json()
    except Exception as e:
        print(f"Lỗi khi lấy thông tin người dùng: {e}")
        traceback.print_exc()
        return None
def GenerateLoginQr(sessions):
    payload = {
        "continue": "https://zalo.me/pc",
        "v": "5.5.7"
    }
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    response = sessions.post(
        "https://id.zalo.me/account/authen/qr/generate",
        headers=headers,
        data=payload
    )
    data = response.json()
    qr_code = data["data"]["image"]
    token = data["data"]["token"]

    if not qr_code:
        return False

    qr_code_data = qr_code.replace("data:image/png;base64,", "")
    qr_code_bytes = base64.b64decode(qr_code_data)
    qr = Image.open(io.BytesIO(qr_code_bytes))
    qr.save("assets/cache/qr_code.png")

    code = data["data"]["code"]
    print(f"QR Code: {code}")
    return code, sessions



def check_session(sessions):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "upgrade-insecure-requests": "1",
        "Referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    try:
        cookies = sessions.cookies
        response = sessions.get(
            "https://id.zalo.me/account/checksession?continue=https%3A%2F%2Fchat.zalo.me%2Findex.html",
            headers=headers,
            cookies=cookies,
        )
        return response
    except Exception as e:
        print(f"Lỗi khi kiểm tra session: {e}")
        traceback.print_exc()
        return None



def get_user_info(sessions):
    headers = {
        "accept": "*/*",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Referer": "https://chat.zalo.me/",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    try:
        response = sessions.get(
            "https://jr.chat.zalo.me/jr/userinfo",
            headers=headers
        )
        return response.json()
    except Exception as e:
        print(f"Lỗi khi lấy thông tin người dùng: {e}")
        traceback.print_exc()
        return None



def waiting_confirm(code, sessions):
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
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        try:
            response = sessions.post(
                "https://id.zalo.me/account/authen/qr/waiting-confirm",
                headers=headers,
                data=confirm_payload,
                timeout=30
            )
            status_data = response.json()
            data = check_session(sessions)
            print(data)

            cookies = sessions.cookies
            if status_data.get("error_code", 1) == 0:
                print("Xác nhận đăng nhập thành công")
                for cookie in cookies:
                    if cookie.name == "zpw_sek":
                        imei = imeiGenerate()
                        cookiejar = {"zpw_sek": cookie.value}
                        data = {
                            "prefix": "?",
                            "imei": imei,
                            "cookie": cookiejar,
                            "active": False,
                        }
                        return data

            time.sleep(5)
            attempts += 1

        except requests.exceptions.Timeout:
            print("Request bị timeout, thử lại...")
            time.sleep(5)
            attempts += 1
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(5)
            traceback.print_exc()
            attempts += 1

    print("Đã vượt quá số lần thử, QR có thể đã hết hạn")
    return None



def waiting_scan(code, sessions):
    check_payload = {
        "code": code,
        "continue": "https://chat.zalo.me/",
        "v": "5.5.7"
    }
    headers = {
        "accept": "*/*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://id.zalo.me",
        "priority": "u=1, i",
        "referer": "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F",
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    print("Đang chờ quét QR code...")
    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        try:
            response = sessions.post(
                "https://id.zalo.me/account/authen/qr/waiting-scan",
                headers=headers,
                data=check_payload,
                timeout=10
            )
            status_data = response.json()

            
            if status_data.get("error_code") == 0:
                print("Đã quét QR code")
                return True
            elif status_data.get("error_code") == 1:
                
                print("Chưa quét QR code")
                time.sleep(3)
                attempts += 1
                continue
            else:
                
                print(f"Lỗi: {status_data}")
                time.sleep(3)
                attempts += 1
                continue

        except requests.exceptions.Timeout:
            print("Request bị timeout, thử lại...")
            time.sleep(3)
            attempts += 1
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(3)
            attempts += 1

    print("Đã vượt quá số lần thử, QR có thể đã hết hạn")
    return False



def authenticate_zalo():
    sessions = SessionHeader()
    if not sessions:
        return None

    sessions = verifyClient(sessions)

    code, sessions = GenerateLoginQr(sessions)

    result = waiting_scan(code, sessions)
    if not result:
        print("Đăng nhập thất bại")

    result = waiting_confirm(code, sessions)

    if result:
        print("Xác thực thành công")
        print(result)

        user_info = get_user_info(sessions)
        if user_info:
            print(f"Thông tin người dùng: {user_info}")

        return sessions

    return None

if __name__ == "__main__":
    authenticate_zalo()