# refresh_cookies.py
# -*- coding: utf-8 -*-
import json
import requests
from bs4 import BeautifulSoup

def get_fresh_cookies():
    """Lấy cookies mới từ Zalo"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Mở trang Zalo
    resp = session.get('https://chat.zalo.me/')
    cookies = session.cookies.get_dict()
    
    return cookies

if __name__ == "__main__":
    cookies = get_fresh_cookies()
    with open('login.json', 'r') as f:
        data = json.load(f)
    data['session_cookies'] = cookies
    with open('login.json', 'w') as f:
        json.dump(data, f, indent=4)
    print("✅ Đã cập nhật cookies!")