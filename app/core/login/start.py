from app.core.login.login import *
from functions.services.hook.core_hook.qr_hook import *
import os

def main():
    try:
        if not check():
            logger.debug("Login data is blankType;")
            qr()
        
        Allbots = LoadAllBotData()
        
        if not Allbots:
            logger.warning("No valid bot data found")
            return

        valid_items = []
        for item in Allbots:
            if item.get("imei") and isinstance(item.get("sessionCookies"), dict) and item.get("sessionCookies") and item.get("status") is True:
                if CheckBotExpiration(item):
                    valid_items.append(item)
        
        if not valid_items:
            logger.warning("No valid bot items found")
            return

        if os.getenv("ZBUG_DEV_MAIN_ONLY", "0") == "1":
            valid_items = [item for item in valid_items if bool(item.get("mainBot", False))]
            if not valid_items:
                logger.warning("Dev mode enabled but no valid mainBot found")
                return
        
        StartThreads(valid_items)
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        eventBoolsShutdown()
    except Exception as e:
        logger.errorMeta(f"Error in starts: {e}")
        import traceback
        traceback.print_exc()
    finally:
        eventBoolsShutdown()

if __name__ == "__main__":
    import atexit
    atexit.register(eventBoolsShutdown)
    main()