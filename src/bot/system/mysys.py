from dto.dtobuilder import *
from functions.services.artistcore.dtoImage import *

def runCmd(cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return (p.stdout or "").strip()
    except Exception:
        return ""

def firstNonEmpty(*vals):
    for v in vals:
        v = (v or "").strip()
        if v:
            return v
    return ""

def readFirstLine(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return (f.readline() or "").strip()
    except Exception:
        return ""

def readCpuModel():
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("model name"):
                    return (line.split(":", 1)[1] if ":" in line else "").strip()
    except Exception:
        pass
    return ""

def readCpuCores():
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            return str(sum(1 for line in f if line.startswith("processor")))
    except Exception:
        return ""

def readLoadAvg():
    s = readFirstLine("/proc/loadavg")
    if not s:
        return ""
    p = s.split()
    return " ".join(p[:3]) if len(p) >= 3 else s

def readMemMb():
    total = used = ""
    try:
        memtotal = memavail = None
        with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    memtotal = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    memavail = int(line.split()[1])
                if memtotal is not None and memavail is not None:
                    break
        if memtotal is not None and memavail is not None and memtotal > 0:
            total = str(memtotal // 1024)
            used = str((memtotal - memavail) // 1024)
    except Exception:
        pass
    return total, used

def dfRoot():
    out = runCmd(["bash", "-lc", "df -h / 2>/dev/null | awk 'NR==2{print $3\"/\"$2\" (\"$5\")\"}'"])
    return out or ""

def osPretty():
    if not os.path.exists("/etc/os-release"):
        return ""
    return runCmd(["bash", "-lc", "source /etc/os-release; echo ${PRETTY_NAME:-$NAME}"])

def parseDfPct():
    try:
        s = runCmd(["bash", "-lc", "df -P / 2>/dev/null | awk 'NR==2{print $5}'"]).strip()
        if s.endswith("%"):
            return int(s[:-1])
    except Exception:
        pass
    return -1

def mySys(this, message, data, userId, threadId, type):
    if os.name == "nt":
        return this.sendMCustom("UNSUPPORTED", "r", "This command is only supported on Linux systems.", userId, threadId, type)
    b = svtBuilder()
    distroId = (b.checkDistro() or {}).get("id") or "unknown"
    waitMessage = this.sendMCustom("WAITING", "y", f"Checking {distroId} system infomation", userId, threadId, type)

    arch = bool(getattr(b, "arch", False))
    ubuntu = bool(getattr(b, "ubuntu", False))

    distro = "arch" if arch else ("ubuntu" if ubuntu else "unknown")
    ok = "OK" if (arch or ubuntu) else "FAIL"

    kernel = platform.release() or ""
    machine = platform.machine() or ""

    env = os.environ
    shell = env.get("SHELL", "") or ""
    de = firstNonEmpty(env.get("XDG_CURRENT_DESKTOP", ""), env.get("DESKTOP_SESSION", ""))
    session = env.get("XDG_SESSION_TYPE", "") or ""
    wayland = "1" if env.get("WAYLAND_DISPLAY") else "0"
    display = "1" if env.get("DISPLAY") else "0"

    which = shutil.which
    pacman = "1" if which("pacman") else "0"
    yay = "1" if which("yay") else "0"
    apt = "1" if which("apt") else "0"
    flatpak = "1" if which("flatpak") else "0"
    systemctl = "1" if which("systemctl") else "0"
    nmcli = "1" if which("nmcli") else "0"
    iw = "1" if which("iw") else "0"
    ip = "1" if which("ip") else "0"
    sensors = "1" if which("sensors") else "0"
    nvidiaSmi = "1" if which("nvidia-smi") else "0"
    lspci = "1" if which("lspci") else "0"

    osRelease = osPretty() or ""
    cpuModel = readCpuModel() or (runCmd(["bash", "-lc", "lscpu | awk -F: '/Model name/ {sub(/^ +/,\"\",$2); print $2; exit}'"]) if which("lscpu") else "")
    cpuCores = readCpuCores() or ""
    cpuLoad = readLoadAvg() or ""

    memTotal, memUsed = readMemMb()
    diskRoot = dfRoot()

    vga = ""
    if lspci == "1":
        vga = firstNonEmpty(
            runCmd(["bash", "-lc", "lspci | grep -E 'VGA compatible controller|3D controller|Display controller' | head -n1 | sed 's/^[^:]*: *//'"]),
            runCmd(["bash", "-lc", "lspci | grep -Ei 'nvidia|amd|intel' | head -n1 | sed 's/^[^:]*: *//'"]),
        )

    gpuDetail = ""
    gpuMem = ""
    tempGpu = ""
    if nvidiaSmi == "1":
        gpuDetail = runCmd(["bash", "-lc", "nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits | head -n1"]) or ""
        gpuMem = runCmd(["bash", "-lc", "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | head -n1 | sed 's/, */\\//'" ]) or ""
        t = runCmd(["bash", "-lc", "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -n1"]) or ""
        tempGpu = f"{t}C" if t else ""

    tempCpu = ""
    if sensors == "1":
        tempCpu = firstNonEmpty(
            runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/Package id 0:/ {print $4; exit}'"]),
            runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/Tctl:/ {print $2; exit}'"]),
            runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/CPU Temperature:/ {print $3; exit}'"]),
        )
        if not tempGpu:
            tempGpu = firstNonEmpty(
                runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/edge:/ {print $2; exit}'"]),
                runCmd(["bash", "-lc", "sensors 2>/dev/null | awk '/GPU Temperature:/ {print $3; exit}'"]),
            )

    upTime = runCmd(["bash", "-lc", "uptime -p 2>/dev/null"]) or ""

    netDefault = runCmd(["bash", "-lc", "ip route 2>/dev/null | awk '/default/ {print $5; exit}'"]) if ip == "1" else ""
    ipv4 = runCmd(["bash", "-lc", "ip -4 addr show 2>/dev/null | awk '/inet /{print $2\" \"$NF}' | head -n3 | tr '\\n' '|' | sed 's/|$//'"]) if ip == "1" else ""
    dns = runCmd(["bash", "-lc", "awk '/^nameserver/{print $2}' /etc/resolv.conf | head -n3 | tr '\\n' ',' | sed 's/,$//'"]) if os.path.exists("/etc/resolv.conf") else ""

    wlanDev = ""
    wifiSsid = ""
    wifiSignal = ""
    if nmcli == "1":
        wlanDev = runCmd(["bash", "-lc", "nmcli -t -f DEVICE,TYPE dev status 2>/dev/null | awk -F: '$2==\"wifi\"{print $1; exit}'"]) or ""
        wifiSsid = runCmd(["bash", "-lc", "nmcli -t -f active,ssid dev wifi 2>/dev/null | awk -F: '$1==\"yes\"{print $2; exit}'"]) or ""
        wifiSignal = runCmd(["bash", "-lc", "nmcli -t -f active,signal dev wifi 2>/dev/null | awk -F: '$1==\"yes\"{print $2; exit}'"]) or ""
    elif iw == "1":
        wlanDev = runCmd(["bash", "-lc", "iw dev 2>/dev/null | awk '/Interface/ {print $2; exit}'"]) or ""

    pingOk = ""
    if which("ping"):
        pingOk = "1" if runCmd(["bash", "-lc", "ping -c1 -W1 1.1.1.1 >/dev/null 2>&1; echo $?"]) == "0" else "0"

    memPct = -1
    try:
        if memTotal and memUsed:
            memPct = int(int(memUsed) * 100 / max(1, int(memTotal)))
    except Exception:
        memPct = -1

    vramPct = -1
    if gpuMem and "/" in gpuMem:
        a, b2 = gpuMem.split("/", 1)
        try:
            vramPct = int(int(a.strip()) * 100 / max(1, int(b2.strip())))
        except Exception:
            vramPct = -1

    diskPct = parseDfPct()

    payload = {
        "bot": {
            "name": getattr(this, "bot", "") or "",
            "uptime": "",
            "version": "",
        },
        "sys": {
            "os": osRelease or "unknown",
            "uptime": upTime or "unknown",
            "cpu": cpuModel or "unknown",
            "cpuCores": cpuCores or "unknown",
            "cpuPct": None,
            "processes": "",
            "ramUsed": f"{memUsed} MB" if memUsed else "unknown",
            "ramTotal": f"{memTotal} MB" if memTotal else "unknown",
            "ramFree": "",
            "ramPct": memPct if memPct >= 0 else None,
            "diskUsed": diskRoot.split("/")[0].strip() if diskRoot and "/" in diskRoot else (diskRoot or "unknown"),
            "diskTotal": "",
            "diskFree": "",
            "diskPct": diskPct if diskPct >= 0 else None,
            "kernel": kernel,
            "arch": machine,
            "session": session,
            "wayland": wayland,
            "x11": display,
            "de": de or "unknown",
            "shell": shell or "unknown",
            "vga": vga or "unknown",
            "nvidia": gpuDetail or "0",
            "vram": gpuMem or "unknown",
            "vramPct": vramPct if vramPct >= 0 else None,
            "tempCpu": tempCpu or "unknown",
            "tempGpu": tempGpu or "unknown",
            "pkg": f"pacman={pacman} yay={yay} apt={apt} flatpak={flatpak} systemctl={systemctl}",
        },
        "net": {
            "iface": netDefault or "unknown",
            "driver": "",
            "proto": "",
            "type": "",
            "sent": "",
            "recv": "",
            "ipv4": ipv4 or "unknown",
            "dns": dns or "unknown",
            "ping": pingOk or "unknown",
            "wlanDev": wlanDev or "unknown",
            "ssid": wifiSsid or "unknown",
            "signal": wifiSignal or "unknown",
        },
        "lines": [
            f"status={ok} distro={distro}",
            f"os={osRelease or 'unknown'}",
            f"kernel={kernel} arch={machine} uptime={upTime or 'unknown'}",
            f"session={session} wayland={wayland} x11={display} de={de or 'unknown'} shell={shell or 'unknown'}",
            f"cpu={cpuModel or 'unknown'} cores={cpuCores or 'unknown'} load={cpuLoad or 'unknown'} tempCpu={tempCpu or 'unknown'}",
            f"memMB={memUsed or 'unknown'}/{memTotal or 'unknown'} diskRoot={diskRoot or 'unknown'}",
            f"vga={vga or 'unknown'}",
            f"nvidia={gpuDetail or '0'} vramMB={gpuMem or 'unknown'} tempGpu={tempGpu or 'unknown'}",
            f"net defaultIf={netDefault or 'unknown'} ipv4={ipv4 or 'unknown'} dns={dns or 'unknown'} ping1.1.1.1={pingOk or 'unknown'}",
            f"wlan dev={wlanDev or 'unknown'} ssid={wifiSsid or 'unknown'} signal={wifiSignal or 'unknown'}",
            f"pkg pacman={pacman} yay={yay} apt={apt} flatpak={flatpak} systemctl={systemctl}",
        ],
    }

    filePath, imgw, imgh = RenderSysTerminal(payload, distro)
    url = (this.uploadImage(filePath, threadId, type) or {}).get("hdUrl") or ""
    if not url:
        return this.sendMSuccess(filePath, userId, threadId, type)
    this.undoMessage(waitMessage.msgId, waitMessage.clientId, threadId, type)
    this.sendImage(imageUrl=url, message=Message(text=None), threadId=threadId, type=type, width=imgw, height=imgh)
    return

dependencies = {
    "name": "fastfetch",
    "permission": 4,
    "description": "System check",
    "cooldown": 5,
    "main": mySys
}
