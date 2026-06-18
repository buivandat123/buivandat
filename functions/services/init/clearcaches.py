from dto.index import *

MediaExts = {
    ".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".flv", ".wmv", ".ts", ".m3u8",
    ".mp3", ".aac", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".wma",
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic"
}

SkipExts = {".txt", ".json", ".log"}

def ClearCache(path="assets/cache"):
    removed = 0
    root = os.path.abspath(path)

    if not os.path.isdir(root):
        return 0

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext in SkipExts or ext not in MediaExts:
                continue

            fp = os.path.join(dirpath, name)
            try:
                os.remove(fp)
                removed += 1
            except:
                pass

    if removed > 0:
        logger.base("Init Clear Caches..!")

    return removed

def StartClearCacheLoop(path="assets/cache", intervalSec=20):
    def Loop():
        while True:
            ClearCache(path)
            time.sleep(intervalSec)

    t = threading.Thread(target=Loop, daemon=True)
    t.start()
    return t