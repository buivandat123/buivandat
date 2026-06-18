import os
import re
import sys
import subprocess
from functions.api.util.logger.logging import logger
from dto.ops import sysOps

class svtBuilder(sysOps):
    def __init__(build):
        super().__init__()
        distro = build.checkDistro()
        distroId = (distro or {}).get("id", "")
        build.arch = distroId == "arch"
        build.ubuntu = distroId == "ubuntu"
        build.pipMap = {
            "Crypto": "pycryptodome",
            "Cryptodome": "pycryptodomex",
            "websocket": "websocket-client",
            "PIL": "Pillow",
            "genai": "google-genai",
            "cv2": "opencv-python",
            "yaml": "PyYAML",
            "bs4": "beautifulsoup4",
            "lxml": "lxml",
            "numpy": "numpy",
            "requests": "requests",
            "aiohttp": "aiohttp",
            "playwright": "playwright",
            "pyzbar": "pyzbar",
            "rembg": "rembg",
            "onnxruntime": "onnxruntime",
        }

    def runCmd(build, cmd):
        return subprocess.run(cmd, shell=True, check=True)

    def cmdExists(build, name):
        return subprocess.run(f"command -v {name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def pkgInstalledPacman(build, name):
        return subprocess.run(f"pacman -Qi {name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def pkgInstalledApt(build, name):
        return subprocess.run(f"dpkg -s {name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def pacman(build):
        if not build.arch:
            return None

        if not build.cmdExists("yay"):
            if not build.cmdExists("git"):
                build.runCmd("sudo pacman -Sy --noconfirm git")
            if not build.cmdExists("makepkg"):
                build.runCmd("sudo pacman -Sy --noconfirm base-devel")

            build.runCmd("cd /tmp && rm -rf yay && git clone https://aur.archlinux.org/yay.git")
            build.runCmd("cd /tmp/yay && makepkg -si --noconfirm")

        pkgs = ["cloudflared", "mariadb", "ffmpeg", "zbar", "fastfetch"]
        missing = [p for p in pkgs if not build.pkgInstalledPacman(p)]
        if missing:
            build.runCmd("yay -S --noconfirm " + " ".join(missing))

        return True

    def apt(build):
        if not build.ubuntu:
            return None

        pkgs = ["cloudflared", "mariadb-server", "ffmpeg", "zbar-tools"]
        missing = [p for p in pkgs if not build.pkgInstalledApt(p)]
        if missing:
            build.runCmd("sudo apt update -y")
            build.runCmd("sudo apt install -y " + " ".join(missing))

        return True

    def parseMissingModule(build, msg):
        m = re.search(r"No module named ['\"]([^'\"]+)['\"]", msg or "")
        return m.group(1) if m else ""

    def moduleToPip(build, mod):
        base = (mod or "").split(".", 1)[0]
        return build.pipMap.get(base, base.replace("_", "-"))

    def installPkg(build, pkg):
        cmd = ["pip3", "install", "-U", pkg, "--break-system-packages"]
        return subprocess.run(cmd).returncode == 0

    def goto(build, path, argv):
        absPath = os.path.abspath(path)
        if not os.path.exists(absPath):
            print(f"file not found: {path}")
            return 1

        installed = set()
        for _ in range(50):
            p = subprocess.run(
                ["python3", absPath, *argv],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if p.returncode == 0:
                if p.stdout:
                    sys.stdout.write(p.stdout)
                return 0

            out = p.stdout or ""
            mod = build.parseMissingModule(out).strip()
            if not mod:
                sys.stderr.write(out)
                return p.returncode

            pkg = build.moduleToPip(mod)
            if pkg in installed:
                sys.stderr.write(f"still failing: {mod} -> {pkg}\n")
                sys.stderr.write(out)
                return p.returncode

            sys.stderr.write(f"missing: {mod} -> installing: {pkg}\n")
            if not build.installPkg(pkg):
                sys.stderr.write(f"install failed: {pkg}\n")
                sys.stderr.write(out)
                return 1

            installed.add(pkg)

        sys.stderr.write("too many retries\n")
        return 1

    def core(build):
        logger.base(f"Build-core decaded")
        build.pacman()
        build.apt()