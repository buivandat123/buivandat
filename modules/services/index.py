# modules/services/index.py
import time
import threading

def restartABot(bot):
    """Restart a bot - chạy thật"""
    try:
        print(f"[Restart] 🔄 Restarting bot: {bot.get('botIntId')}")
        
        # Lấy thông tin từ bot
        imei = bot.get("imei")
        session_cookies = bot.get("sessionCookies")
        prefix = bot.get("prefix", "!")
        mainBot = bot.get("mainBot", False)
        username = bot.get("username")
        botIntId = bot.get("botIntId")
        filePath = bot.get("filePath")
        login = bot.get("login", 24)
        
        # Import RunBot
        from app.core.login.login import RunBot
        
        # Chạy bot trong thread mới
        thread = threading.Thread(
            target=RunBot,
            args=(imei, session_cookies, prefix, mainBot, username, botIntId, True, filePath, login, None),
            daemon=True
        )
        thread.start()
        
        print(f"[Restart] ✅ Bot {botIntId} đã được khởi động lại")
        return True
    except Exception as e:
        print(f"[Restart] ❌ Lỗi: {e}")
        return False

def shutdownABot(bot):
    """Shutdown a bot - dừng thật"""
    try:
        print(f"[Shutdown] 🛑 Stopping bot: {bot.get('botIntId')}")
        
        # Lấy client từ getClient
        from app.core.login.client import getClient
        botIntId = bot.get("botIntId")
        isMain = bot.get("mainBot", False)
        
        if isMain:
            entry = getClient.getMain()
        else:
            entry = getClient.get(str(botIntId))
        
        if entry and entry.client:
            # Dừng bot
            if hasattr(entry.client, "stopListening"):
                entry.client.stopListening()
            elif hasattr(entry.client, "bools"):
                b = entry.client.bools
                if b:
                    b.shutdown(wait=False)
            if hasattr(entry.client, "listening"):
                entry.client.listening = False
            if hasattr(entry.client, "_bot_enabled"):
                entry.client._bot_enabled = False
        
        print(f"[Shutdown] ✅ Bot {botIntId} đã được dừng")
        return True
    except Exception as e:
        print(f"[Shutdown] ❌ Lỗi: {e}")
        return False
