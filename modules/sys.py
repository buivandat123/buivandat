# modules/sys.py
# -*- coding: utf-8 -*-
import os
import subprocess
import platform
import re
from datetime import datetime

from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    "version": "1.0.0",
    "credits": "kryzis X TXA",
    "description": "Lấy thông tin hệ thống Termux và thiết bị",
    "power": "Admin"
}

def _sty(text, color):
    """Style cho tin nhắn"""
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size="9", auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def sty_ok(t):   return _sty(t, "#15A85F")
def sty_warn(t): return _sty(t, "#F7B503")
def sty_err(t):  return _sty(t, "#DB342E")
def sty_info(t): return _sty(t, "#00BFFF")

def _reply(client, msg_obj, tid, ttype, text, sty_fn):
    client.replyMessage(Message(text=text, style=sty_fn(text)), msg_obj, tid, ttype)

def format_size(size_bytes):
    """Định dạng kích thước"""
    if size_bytes <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def get_device_info():
    """Lấy thông tin thiết bị Android"""
    info = {}
    
    # Đọc build.prop
    props = {}
    build_paths = ['/system/build.prop', '/vendor/build.prop', '/product/build.prop']
    for path in build_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if '=' in line:
                            key, val = line.strip().split('=', 1)
                            props[key] = val
            except:
                pass
    
    info['brand'] = props.get('ro.product.brand', props.get('ro.product.manufacturer', 'Unknown'))
    info['model'] = props.get('ro.product.model', props.get('ro.product.device', 'Unknown'))
    info['device'] = props.get('ro.product.device', 'Unknown')
    info['android'] = props.get('ro.build.version.release', 'Unknown')
    info['sdk'] = props.get('ro.build.version.sdk', 'Unknown')
    
    # CPU
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'Hardware' in line:
                    info['cpu'] = line.split(':', 1)[1].strip()
                elif 'processor' in line:
                    if 'cores' not in info:
                        info['cores'] = 0
                    info['cores'] += 1
    except:
        info['cpu'] = 'Unknown'
        info['cores'] = '?'
    
    # RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    kb = int(re.search(r'(\d+)', line).group(1))
                    info['ram'] = kb * 1024
                elif 'MemAvailable' in line:
                    kb = int(re.search(r'(\d+)', line).group(1))
                    info['ram_free'] = kb * 1024
    except:
        pass
    
    # Pin
    try:
        battery_path = '/sys/class/power_supply/battery/'
        if os.path.exists(battery_path):
            cap_file = os.path.join(battery_path, 'capacity')
            if os.path.exists(cap_file):
                with open(cap_file, 'r') as f:
                    info['battery'] = f.read().strip() + '%'
            
            temp_file = os.path.join(battery_path, 'temp')
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = int(f.read().strip()) / 10
                    info['temp'] = f"{temp}°C"
    except:
        pass
    
    return info

def get_termux_info():
    """Lấy thông tin Termux"""
    info = {'is_termux': False}
    
    if not os.path.exists('/data/data/com.termux'):
        return info
    
    info['is_termux'] = True
    
    # Storage
    try:
        stat = os.statvfs('/data/data/com.termux')
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        info['storage_total'] = total
        info['storage_free'] = free
    except:
        pass
    
    # Packages
    try:
        result = subprocess.check_output(['pkg', 'list-installed'], text=True, stderr=subprocess.DEVNULL, timeout=5)
        lines = [l for l in result.split('\n') if l and not l.startswith('Listing')]
        info['packages'] = len(lines)
    except:
        info['packages'] = 0
    
    return info

def handle_sys(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh sys"""
    
    device = get_device_info()
    termux = get_termux_info()
    
    lines = []
    lines.append("📱 THÔNG TIN HỆ THỐNG")
    lines.append("")
    lines.append(f"▪️ Hãng    : {device.get('brand', '?')}")
    lines.append(f"▪️ Model   : {device.get('model', '?')}")
    lines.append(f"▪️ Mã máy  : {device.get('device', '?')}")
    lines.append("")
    lines.append(f"▪️ Android : {device.get('android', '?')}")
    lines.append(f"▪️ SDK     : {device.get('sdk', '?')}")
    lines.append("")
    lines.append(f"▪️ CPU     : {device.get('cpu', '?')[:30]}")
    lines.append(f"▪️ Lõi     : {device.get('cores', '?')}")
    lines.append("")
    
    if device.get('ram'):
        ram_total = device.get('ram', 0)
        ram_free = device.get('ram_free', 0)
        ram_used = ram_total - ram_free
        ram_percent = (ram_used / ram_total) * 100 if ram_total > 0 else 0
        lines.append(f"▪️ RAM     : {format_size(ram_used)}/{format_size(ram_total)} ({ram_percent:.0f}%)")
        lines.append("")
    
    if device.get('battery'):
        lines.append(f"▪️ Pin     : {device.get('battery', '?')}")
        if device.get('temp'):
            lines.append(f"▪️ Nhiệt   : {device.get('temp', '?')}")
        lines.append("")
    
    if termux.get('is_termux'):
        lines.append("📦 TERMUX")
        if termux.get('packages'):
            lines.append(f"▪️ Gói     : {termux.get('packages', 0)}")
        if termux.get('storage_total'):
            total = termux.get('storage_total', 0)
            free = termux.get('storage_free', 0)
            used = total - free
            percent = (used / total) * 100 if total > 0 else 0
            lines.append(f"▪️ Storage : {format_size(used)}/{format_size(total)} ({percent:.0f}%)")
        lines.append("")
    
    now = datetime.now()
    lines.append(f"⏰ {now.strftime('%H:%M:%S %d/%m/%Y')}")
    
    _reply(client, message_object, thread_id, thread_type, "\n".join(lines), sty_info)

def LIGHT():
    return {"sys": handle_sys}