from dto.index import *
from src.bot.multibot.botManager import *
from app.core.login.client import getClient
from functions.engine.data.data import databaseReader

PublicDir = os.path.abspath(os.path.join(os.path.dirname(__file__), "website"))
app = Flask("web-services", static_folder=None)
app.secret_key = os.environ.get("EBUG_SECRET", "ebug-secret-dev")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
Lock = threading.Lock()

_DB_DEFAULT = {
    "host": "127.0.0.1",
    "port": 27017,
    "user": "",
    "password": "",
    "database": "main_data",
    "authSource": "admin",
    "create_db": True,
    "collections": {
        "logger": "loggerTable",
    },
}


def GetDbConfig(refresh=False):
    global DbConfig
    if refresh:
        cfg = databaseReader() or {}
        if not isinstance(cfg, dict):
            cfg = {}
        merged = dict(_DB_DEFAULT)
        merged.update({k: v for k, v in cfg.items() if k not in ["collections", "tableSQL"]})
        colls = dict(_DB_DEFAULT.get("collections") or {})
        colls_cfg = cfg.get("collections") or cfg.get("tableSQL") or {}
        if isinstance(colls_cfg, dict):
            colls.update(colls_cfg)
        merged["collections"] = colls
        DbConfig = merged
    return dict(DbConfig)


DbConfig = dict(_DB_DEFAULT)
GetDbConfig(refresh=True)
