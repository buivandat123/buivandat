from app.library.comp import *
from functions.services.hook.core_hook.config_core import *

def check() -> bool:
    try:
        if not os.path.exists(mainLogin):
            return False
        data = jsonLoader(mainLogin)
        if "data" not in data or not data["data"]:
            return False
        valid_items = [
            item for item in data["data"]
            if item.get("imei")
            and isinstance(item.get("sessionCookies"), dict)
            and item.get("sessionCookies")
            and item.get("status") is True
        ]
        return len(valid_items) > 0
    except Exception as e:
        logger.errorMeta(f"Lỗi khi kiểm tra dữ liệu đăng nhập: {e}")
        return False

def addcf(qr_data: Dict, is_main_bot: bool = True) -> bool:
    try:
        sessionCookies = qr_data.get("cookie", {})
        new_entry = {
            "username": None,
            "botIntId": None,
            "imei": qr_data.get("imei"),
            "prefix": qr_data.get("prefix", "?"),
            "sessionCookies": sessionCookies,
            "mainBot": is_main_bot,
            "status": True
        }
        
        if is_main_bot:
            
            data = jsonLoader(mainLogin)
            if "data" not in data:
                data["data"] = []
            data["data"].append(new_entry)
            saveJson(mainLogin, data)
            logger.info("Đã thêm tài khoản chính vào assets/config/login.json")
        else:
            
            account_dir = os.path.join("assets", "config", "multibot")
            os.makedirs(account_dir, exist_ok=True)
            
            existing_files = [f for f in os.listdir(account_dir) if f.endswith("-login.json")]
            next_index = len(existing_files) + 1
            account_file = os.path.join(account_dir, f"{next_index}-login.json")
            account_data = [new_entry]
            saveJson(account_file, account_data)
            logger.info(f"Đã thêm tài khoản phụ vào {account_file}")
        
        return True
    except Exception as e:
        logger.errorMeta(f"Lỗi khi thêm tài khoản vào config: {e}")
        return False

def qr():
    qr_path = "assets/cache/qr_code.png"
    try:
        logger.info("Đang tạo mã QR code...")
        sessions = SessionHeader()
        if not sessions:
            logger.errorMeta("Không thể khởi tạo session")
            return False
        sessions = verifyClient(sessions)
        code, sessions = GenerateLoginQr(sessions)
        if not code:
            logger.errorMeta("Không thể tạo QR code")
            return False
        logger.info(f"QR code đã được tạo: {qr_path}")
        logger.info(f"Mã QR: {code}")
        result = waiting_scan(code, sessions)
        if not result:
            logger.errorMeta("Đăng nhập thất bại")
            if os.path.exists(qr_path):
                os.remove(qr_path)
            return False
        logger.info("Đang chờ xác nhận đăng nhập...")
        qr_data = waiting_confirm(code, sessions)
        if qr_data:
            logger.info("Xác thực thành công")
            if os.path.exists(qr_path):
                os.remove(qr_path)
                logger.info("Đã xóa QR code")
            if addcf(qr_data):
                logger.info("Đã lưu thông tin đăng nhập vào config")
                return True
            else:
                logger.errorMeta("Không thể lưu thông tin đăng nhập")
                return False
        else:
            logger.errorMeta("Xác thực thất bại")
            if os.path.exists(qr_path):
                os.remove(qr_path)
            return False
    except Exception as e:
        logger.errorMeta(f"Lỗi trong quá trình đăng nhập QR: {e}")
        if os.path.exists(qr_path):
            os.remove(qr_path)
        import traceback
        traceback.print_exc()
        return False