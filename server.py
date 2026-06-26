# server.py
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from flask import Flask

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'app/templates'),
    static_folder=os.path.join(BASE_DIR, 'app/static')
)
app.secret_key = "zbug_secret_key_2024"

from app.core.server import init_routes
init_routes(app)

def start_cloudflare_tunnel():
    """Chạy Cloudflare tunnel trong nền"""
    try:
        # Kiểm tra cloudflared
        check = subprocess.run(["which", "cloudflared"], capture_output=True, text=True)
        if check.returncode != 0:
            print("⚠️ cloudflared chưa được cài đặt!")
            print("📌 Cài đặt: pkg install cloudflared")
            return None
        
        # Chạy tunnel
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Đọc và in URL
        for line in iter(proc.stdout.readline, ''):
            import re
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                print(f"\n✅ Cloudflare Tunnel URL: {match.group(0)}")
                print("📌 Dùng link này để truy cập web\n")
                return match.group(0)
            print(line.strip())
        
        return None
    except Exception as e:
        print(f"❌ Lỗi Cloudflare: {e}")
        return None

if __name__ == "__main__":
    os.makedirs("asset/config/multibot", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    print("""
╔═══════════════════════════════════════════╗
║   🚀 BOT MANAGER WEB SERVER              ║
║   http://localhost:5000                  ║
║   Admin: /admin  (pass: admin123)        ║
║   Bot:   /bot/<id>/login                 ║
║   Cloudflare: tự động tạo link public    ║
╚═══════════════════════════════════════════╝
    """)
    
    # Chạy Cloudflare tunnel trong thread riêng
    import threading
    tunnel_thread = threading.Thread(target=start_cloudflare_tunnel, daemon=True)
    tunnel_thread.start()
    
    # Chạy web server
    app.run(host='0.0.0.0', port=5000, debug=True)