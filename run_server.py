#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.core.server import Open

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════╗
║   🚀 BOT MANAGER WEB SERVER              ║
║   Starting server...                      ║
╚═══════════════════════════════════════════╝
    """)
    
    Open()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Server stopped")
