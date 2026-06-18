import os
import platform

class sysOps:
    def __init__(sys):
        sys.info = platform.uname()
        sys.is_linux = sys.info.system == "Linux"
        sys.distro_cache = None

    def checkKernel(sys):
        if not sys.is_linux:
            return {}
        return {
            "kernel_name": sys.info.system,
            "kernel_release": sys.info.release,
            "kernel_version": sys.info.version,
            "machine": sys.info.machine
        }

    def checkDistro(sys):
        if not sys.is_linux:
            return {}

        if sys.distro_cache is not None:
            return sys.distro_cache

        path = "/etc/os-release"
        if not os.path.exists(path):
            sys.distro_cache = {}
            return sys.distro_cache

        data = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k] = v.strip().strip('"')

        sys.distro_cache = {
            "id": data.get("ID"),
            "name": data.get("NAME"),
            "pretty_name": data.get("PRETTY_NAME"),
            "id_like": data.get("ID_LIKE"),
            "version": data.get("VERSION"),
            "version_id": data.get("VERSION_ID"),
            "codename": data.get("VERSION_CODENAME")
        }
        return sys.distro_cache