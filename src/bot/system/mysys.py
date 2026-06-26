# src/bot/system/mysys.py
import os
import subprocess
import platform

def readMemMb():
    try:
        import psutil
        mem = psutil.virtual_memory()
        return mem.total // (1024 * 1024), mem.used // (1024 * 1024)
    except:
        return 4096, 2048

def osPretty():
    return platform.system() or "Linux"

def readCpuModel():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except:
        pass
    return "Unknown"

def readCpuCores():
    try:
        return os.cpu_count() or 4
    except:
        return 4

def readLoadAvg():
    try:
        with open("/proc/loadavg", "r") as f:
            return f.read().strip()
    except:
        return "0.00 0.00 0.00"

def runCmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

def dfRoot():
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            return lines[1].split()[1:]
    except:
        pass
    return "unknown"

def parseDfPct():
    try:
        result = subprocess.run(["df", "/"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) > 4:
                return int(parts[4].replace("%", ""))
    except:
        pass
    return None

def firstNonEmpty(*args):
    for arg in args:
        if arg and str(arg).strip():
            return str(arg).strip()
    return "unknown"
