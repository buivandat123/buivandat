from functions.engine.data.data import ensure_dir
from app.library.comp import *
    
def saveJson(filename: str, data: Dict) -> None:
    with lock:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.errorMeta(f"Lỗi khi lưu dữ liệu vào {filename}: {e}")

def jsonLoader(filename: str) -> Dict:
    if not os.path.exists(filename):
        try:
            ensure_dir(os.path.dirname(filename))
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        except:
            pass
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.errorMeta(f"Invalid JSON: {filename}")
        return {}
    
def saveConfigBot(username: str, botIntId: str, imei: str) -> None:
    with lock:
        try:
            import os
            updated = False
            
            
            data = jsonLoader(mainLogin)
            if "data" not in data:
                data["data"] = []
            
            for user in data["data"]:
                if user.get("imei") == imei or user.get("botIntId") == botIntId:
                    user["username"] = username
                    user["botIntId"] = botIntId
                    with open(mainLogin, "w", encoding="utf-8") as file:
                        json.dump(data, file, indent=4, ensure_ascii=False)
                    updated = True
                    break
                
            if not updated:
                account_dir = os.path.join("assets", "config", "multibot")
                if os.path.exists(account_dir):
                    for filename in os.listdir(account_dir):
                        if filename.endswith("-login.json"):
                            account_file = os.path.join(account_dir, filename)
                            try:
                                with open(account_file, "r", encoding="utf-8") as f:
                                    account_data = json.load(f)
                                
                                
                                data_list = account_data
                                if isinstance(account_data, dict) and "data" in account_data:
                                    data_list = account_data["data"]
                                
                                if isinstance(data_list, list):
                                    for user in data_list:
                                        if user.get("imei") == imei or user.get("botIntId") == botIntId:
                                            user["username"] = username
                                            user["botIntId"] = botIntId
                                            
                                            if isinstance(account_data, dict) and "data" in account_data:
                                                account_data["data"] = data_list
                                            else:
                                                account_data = data_list
                                            with open(account_file, "w", encoding="utf-8") as file:
                                                json.dump(account_data, file, indent=4, ensure_ascii=False)
                                            updated = True
                                            break
                            except Exception as e:
                                logger.errorMeta(f"Error reading account file {account_file}: {e}")
                        
                        if updated:
                            break
            
            if not updated:
                logger.warning(f"Không tìm thấy bot với imei={imei} hoặc botIntId={botIntId} để update username")
        except Exception as e:
            logger.errorMeta(f"Lỗi khi cập nhật username vào login.json: {e}")