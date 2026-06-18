from app.library.comp import *
from functions.services.hook.core_hook.config_core import *

BotManagerConfigPath = "assets/config/bot-manager-database.json"

def loadBotManager():
    return jsonLoader(BotManagerConfigPath) or {}

def botManagerSave(cfg):
    ensure_dir(os.path.dirname(BotManagerConfigPath))
    saveJson(BotManagerConfigPath, cfg)

def setGroupLink(this, threadId):
    try:
        res = this.getGroupLink(threadId) or {}
        data = res.get("data") if isinstance(res, dict) else None
        link = data.get("link") if isinstance(data, dict) else None
        return str(link or "").strip() or None
    except:
        return None

def dataGroup(cfg):
    dg = cfg.get("dataGroup")
    if isinstance(dg, dict):
        return dg
    dg = {}
    cfg["dataGroup"] = dg
    return dg

def NormalizeBotItem(BotItem: Dict) -> Dict:
    return BotItem

def ExtractSessionCookies(BotItem: Dict) -> Dict:
    Sc = BotItem.get("sessionCookies")
    if isinstance(Sc, dict) and Sc:
        return Sc
    return {}

def ReadLoginJson(Path: str) -> List[Dict]:
    try:
        with open(Path, "r", encoding="utf-8") as f:
            Data = json.loads(f.read() or "[]")
        
        
        if isinstance(Data, list):
            return Data
        elif isinstance(Data, dict) and "data" in Data:
            if isinstance(Data["data"], list):
                return Data["data"]
        return []
    except Exception as e:
        logger.errorMeta(f"Failed to read login json: {e}")
        return []

def WriteLoginJson(Path: str, Data: List[Dict]) -> None:
    try:
        with open(Path, "w", encoding="utf-8") as f:
            f.write(json.dumps(Data, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    except Exception as e:
        logger.errorMeta(f"Failed to write login json: {e}")

def CheckBotExpiration(BotItem: Dict) -> bool:
    Exp = BotItem.get("ExpiredTime")
    if not Exp:
        return True
    try:
        from datetime import datetime
        ExpiryDate = datetime.strptime(Exp, "%H:%M:%S/%d/%m/%Y")
        Now = datetime.now()
        if Now > ExpiryDate:
            BotItem["status"] = False
            Username = BotItem.get("username", "Unknown")
            logger.warning(f"Bot {Username} has expired ({Exp}). Auto disabled.")
            return False
        return True
    except Exception as e:
        logger.errorMeta(f"Failed to check expiration: {e}")
        return True
    
def ClearSessionCookiesInConfig(Item: Dict) -> None:
    try:
        if Item.get("mainBot"):
            path = "assets/config/login.json"
            data = jsonLoader(path, {})
            arr = data.get("data", [])
            for it in arr:
                if it.get("imei") == Item.get("imei"):
                    it["sessionCookies"] = {}
            WriteLoginJson(path, arr)
            return

        accountDir = os.path.join("assets", "config", "multibot")
        if not os.path.exists(accountDir):
            return

        for fn in os.listdir(accountDir):
            if not fn.endswith("-login.json"):
                continue
            fp = os.path.join(accountDir, fn)
            arr = ReadLoginJson(fp)
            changed = False
            for it in arr:
                if it.get("botIntId") == Item.get("botIntId") or it.get("imei") == Item.get("imei"):
                    it["sessionCookies"] = {}
                    changed = True
            if changed:
                WriteLoginJson(fp, arr)
                return
    except Exception as e:
        logger.errorMeta(f"ClearSessionCookies failed: {e}")

def NormalizeBotItem(BotItem: Dict) -> Dict:
    return BotItem

def LoadAllBotData() -> List[Dict]:
    Allbots = []

    try:
        os.makedirs(os.path.join("assets", "config", "multibot"), exist_ok=True)
    except Exception as e:
        logger.errorMeta(f"Failed to create config directories: {e}")

    try:
        mainPath = "assets/config/login.json"
        if os.path.exists(mainPath):
            main_data = jsonLoader(mainPath)
            if "data" in main_data and isinstance(main_data["data"], list):
                for item in main_data["data"]:
                    if isinstance(item, dict):
                        item["mainBot"] = True
                        item["filePath"] = mainPath
                        Allbots.append(NormalizeBotItem(item))
    except Exception as e:
        logger.errorMeta(f"Failed to load main bot data: {e}")

    try:
        account_dir = os.path.join("assets", "config", "multibot")
        if os.path.exists(account_dir):
            for filename in os.listdir(account_dir):
                if filename.endswith("-login.json"):
                    account_file = os.path.join(account_dir, filename)
                    try:
                        account_data = ReadLoginJson(account_file)
                        for item in account_data:
                            if isinstance(item, dict):
                                item["mainBot"] = False
                                item["filePath"] = account_file
                                Allbots.append(NormalizeBotItem(item))
                    except Exception as e:
                        logger.errorMeta(f"Failed to load account data from {account_file}: {e}")
    except Exception as e:
        logger.errorMeta(f"Failed to load account bot data: {e}")

    return Allbots

def ensureBotManagerData(cfg):
    arr = cfg.get("data")
    if isinstance(arr, list):
        return arr
    arr = []
    cfg["data"] = arr
    return arr

def NormalizePath(p):
    s = str(p or "").strip().replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    return s

def UpsertBotManagerRunning(uid, mainBot, filePath):
    try:
        cfg = loadBotManager()
        arr = ensureBotManagerData(cfg)

        uid = str(uid or "").strip()
        filePath = NormalizePath(filePath)
        mainBot = bool(mainBot)

        if not uid or not filePath:
            return

        for it in arr:
            if not isinstance(it, dict):
                continue
            itUid = str(it.get("this.uid") or "").strip()
            itMain = bool(it.get("this.mainBot"))
            itPath = NormalizePath(it.get("filePath"))
            
            if itUid == uid and itMain == mainBot and itPath == filePath:
                return

        item = {
            "this.uid": uid,
            "this.mainBot": mainBot,
            "filePath": filePath
        }

        newArr = []
        for it in arr:
            if not isinstance(it, dict):
                continue
            itUid = str(it.get("this.uid") or "").strip()
            itMain = bool(it.get("this.mainBot"))
            itPath = NormalizePath(it.get("filePath"))

            if (itUid == uid and itMain == mainBot) or (itPath == filePath):
                continue

            if itPath:
                it["filePath"] = itPath
            newArr.append(it)

        newArr.append(item)
        cfg["data"] = newArr
        botManagerSave(cfg)
    except Exception as e:
        logger.errorMeta(f"UpsertBotManagerRunning failed: {e}")
        