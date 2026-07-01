import os
import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from asset.config import get_uptime

admin   = "Lê Hoàng Giang メ Light"
version = "1.2.0"

des = {
    'version': "1.0.0",
    'credits': "kryzis X TXA",
    'description': "Menu bot - Khong can prefix",
    'power': "Thành viên"
}

# ============ THÊM/XÓA LỆNH Ở ĐÂY ============
COMMANDS = [
    ("menu",        "hien thi menu"),
    ("reload",      "khoi dong lai bot"),
    ("upcomunity",  "up box len cong dong"),
    ("prefix -new", "thay doi prefix bot"),
    ("info",        "check thong tin user"),
    ("send",        "gui tin nhan"),
    ("ifgr",        "check thong tin nhom"),
    ("join",        "join link box chi dinh"),
    ("admin",       "quan li admin"),
    ("creategroup", "tao nhom moi"),
    ("setnamegr",   "doi ten nhom"),
    ("kick",        "kick thanh vien"),
    ("block",       "chan nguoi dung"),
    ("unblock",     "mo chan nguoi dung"),
    ("transferkey", "chuyen quyen truong nhom"),
    ("friends",     "quan ly ban be"),
    ("phonhom",     "them/xoa pho nhom"),
    ("setavt",      "thay doi anh dai dien"),
    ("callgroup",   "cuoc goi nhom"),
    ("groupsetting","menu quan ly box"),
    ("poll",        "tao/ket thuc poll"),
    ("group",       "quan ly cac nhom co mat bot"),
]
# ==============================================

FONT_DIR    = "modules/cache/font"
VALID_SIZES = {str(i) for i in range(1, 14)}
DEFAULT_SIZE = "1"

def _load_font_size() -> str:
    try:
        if not os.path.isdir(FONT_DIR):
            return DEFAULT_SIZE
        files = [f for f in os.listdir(FONT_DIR) if os.path.isfile(os.path.join(FONT_DIR, f))]
        if not files:
            return DEFAULT_SIZE
        chosen = sorted(files)[0]
        with open(os.path.join(FONT_DIR, chosen), "r", encoding="utf-8") as f:
            data = json.load(f)
        size = str(data.get("size", DEFAULT_SIZE))
        return size if size in VALID_SIZES else DEFAULT_SIZE
    except Exception:
        return DEFAULT_SIZE

def handle_menu(message, message_object, thread_id, thread_type, author_id, client):
    # Lay prefix hien tai
    prefix = client.settings.get("prefix", ".")
    font_size = _load_font_size()

    header = (
        f"admin: {admin}\n"
        f"version: {version}\n"
        f"total Menu: {len(COMMANDS)}\n"
        f"uptime: {get_uptime()}\n"
        f"prefix: {prefix}\n"
        f"___________________\n"
    )
    cmd_lines = "\n".join([f"{prefix}{cmd} - {desc}" for cmd, desc in COMMANDS])
    text = header + cmd_lines + "\n"

    style_list = [
        MessageStyle(offset=0, length=len(text), style="font", size=font_size, auto_format=False)
    ]

    search_start = 0
    for cmd, _ in COMMANDS:
        full_cmd = f"{prefix}{cmd}"
        try:
            o = text.index(full_cmd, search_start)
            style_list.append(MessageStyle(offset=o, length=len(full_cmd), style="color", color="#15A85F", auto_format=False))
            style_list.append(MessageStyle(offset=o, length=len(full_cmd), style="bold", auto_format=False))
            search_start = o + len(full_cmd)
        except ValueError:
            pass

    client.replyMessage(
        Message(text=text, style=MultiMsgStyle(style_list)),
        message_object, thread_id=thread_id,
        thread_type=thread_type, ttl=120000
    )

def Kryzis():
    """Export cho noprefix - tu dong chay khi go 'menu' hoac 'help'"""
    return {
        "menu": handle_menu,
        "me nu": handle_menu,
        "hiện cái menu hộ bố": handle_menu,
        "menu đâu cưng": handle_menu,
        "hiện menu ra cho người ta kìa": handle_menu,
        "help": handle_menu,
        "mầy show cái menu bot ra": handle_menu,
        "cak": handle_menu,
        "cưng ơi": handle_menu
    }