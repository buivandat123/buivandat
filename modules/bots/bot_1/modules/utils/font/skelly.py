# modules/utils/font/skelly.py
import base64

OBF_KEY = "k9Z!p2@v"

def skellyLook(s):
    pad = "=" * (-len(s) % 4)
    raw = base64.urlsafe_b64decode((s + pad).encode())
    k = OBF_KEY.encode()
    out = bytes(raw[i] ^ k[i % len(k)] for i in range(len(raw)))
    return out.decode()