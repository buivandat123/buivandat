#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import json
import time

# Thêm đường dẫn gốc vào sys.path
BASE_DIR = "/storage/emulated/0/download/kryzis"
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

# Import các module cần thiết
try:
    from main import MainBot
    from asset.config import API_KEY, SECRET_KEY
except ImportError as e:
    print(f"[Bot] Lỗi import: {e}")
    print("[Bot] Đang thử import từ đường dẫn khác...")
    # Thử import trực tiếp
    sys.path.insert(0, os.path.join(BASE_DIR, "app"))
    sys.path.insert(0, os.path.join(BASE_DIR, "modules"))
    from main import MainBot
    from asset.config import API_KEY, SECRET_KEY

# Cấu hình bot
bot_config = {
    "api_key": API_KEY,
    "secret_key": SECRET_KEY,
    "imei": "84b2fd2b-4db7-439f-97ca-8a05b205671d-a16ddaab909d2cf27fce353f26dd2ff2",
    "session_cookies": {"nl_b04af40bb0e193acf8a9877592394ada": "tzaoLC8i6lt5qJ5Ho2eG_iNLFqpOT72xbD8T1penVG", "zpdid": "41RxbrFsgJiG5v6KKlh4E1KTbvvH-i4s", "zlogin_session": "kW4JGLyjCnIxFnDDLXTbH-Tj2KLL4cz1xMuNKmHJOLccBmHQ25DeNwOc244UM7uC", "_zlang": "vn", "zpsid": "eMKnVcAlVqAZUYmFGw5m1yylUrLQe7G3pIraKK7TB0kC9Y0YHSbF2ByUI28mvJCtv3auOXAnS37uVpyb4l1LBFCh6GCVqt4qqYW150EhSoZLTImp79f35m", "__zi": "3000.QOBlzDCV2uGerkFzm0LJq6FNv_d21nxKOTYf-iSD6TTdtghx.1", "zpw_sek": "Ye_R.451751557.a0.YLRBUo1JVGMbVP0V0LDz1Ljn66u2QLz7PMSeRMa5Fszu10z0OX8KQ1SGILrNRa0dNIB4KNC5kW-oKiwB6Zbz1G"}
}

print(f"[Bot] Đang khởi động bot {bot_config['imei']}...")
print(f"[Bot] Prefix: <")

try:
    # Khởi tạo bot
    bot = MainBot(**bot_config)
    bot.settings = {"prefix": "<"}
    bot._bot_enabled = True
    
    print("[Bot] Bot đã sẵn sàng, bắt đầu listen...")
    bot.listen()
    
except KeyboardInterrupt:
    print("[Bot] Bot đã dừng bởi Ctrl+C")
except Exception as e:
    print(f"[Bot] Lỗi: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("[Bot] Bot đã kết thúc")
