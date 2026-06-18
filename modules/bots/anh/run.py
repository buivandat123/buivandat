# -*- coding: utf-8 -*-
import sys
import os
import json

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

# Import canvas as requested by user
from modules.canvas import *

from main import MainBot
import asset.config

# Load config
with open(os.path.join(current_dir, "bot_config.json"), "r", encoding="utf-8") as f:
    cfg = json.load(f)

# Patch configuration
asset.config.IMEI = cfg.get("IMEI")
asset.config.SESSION_COOKIES = cfg.get("SESSION_COOKIES")
asset.config.PREFIX = cfg.get("PREFIX")
asset.config.ADMIN = cfg.get("ADMIN")

# Start client
try:
    client = MainBot(asset.config.API_KEY, asset.config.SECRET_KEY, asset.config.IMEI, asset.config.SESSION_COOKIES)
    client.settings["prefix"] = asset.config.PREFIX
    client.ADMIN = str(asset.config.ADMIN)
    client.listen()
except KeyboardInterrupt:
    print("\n👋 Đang dừng bot con sạch sẽ (Ctrl+C)... Hẹn gặp lại!")
    sys.exit(0)
