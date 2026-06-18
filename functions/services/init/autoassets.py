from dto.index import *

def getDir() -> None:
    dirs = (
        "assets/cache",
        "assets/storage",
        "assets/log"
    )
    logger.base("Assets ready OK")
    for path in dirs:
        os.makedirs(path, exist_ok=True)