import os
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

class Logging:
    def _now(self):
        return datetime.now().strftime("%H:%M:%S")

    def _print(self, level, color, text):
        print(f"{color}[{self._now()}] [{level}]{Style.RESET_ALL} {text}")

    def info(self, msg):
        self._print("INFO", Fore.CYAN, msg)

    def success(self, msg):
        self._print("OK", Fore.GREEN, msg)

    def warning(self, msg):
        self._print("WARN", Fore.YELLOW, msg)

    def error(self, msg):
        self._print("ERR", Fore.RED, msg)

    def prefixcmd(self, msg):
        self._print("CMD", Fore.MAGENTA, msg)