# main.py
import os, sys, json, time, math, io, shutil, traceback, threading, subprocess, signal, requests
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

from zlapi import ZaloAPI
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from zlapi.logging import Logging

from asset.config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES, ADMIN, PREFIX
from Kryzis import CommandHandler, check_is_admin, schedule_delete, get_delete_delay
from modules.rs import send_reset_success_message
from modules.scl import Kryzis as scl_module, user_states as scl_user_states, handle_message as scl_handle_message
from modules.lqskin import handle_skin_choice, user_states
from modules.sleep import update_activity, is_sleeping, wake_up
from modules.mute import is_muted
from modules.kw import on_message as kw_on_message

logger = Logging()
executor = ThreadPoolExecutor(max_workers=12)

# ─── FILES ────────────────────────────────────────────
NOTIFY_FILE = "modules/cache/notify.json"
NOTIFY_ADM_FILE = "modules/cache/notify_admin.json"
NS_FILE = "modules/cache/nameserver.json"
MUTE_FILE = "modules/cache/muted_users.json"
APPROVE_FILE = "modules/cache/approve_groups.json"
SPAM_FILE = "modules/cache/spam_blocked.json"
WARN_FILE = "modules/cache/warnings.json"
BOTS_DIR = "modules/bots"
os.makedirs(BOTS_DIR, exist_ok=True)

# ─── SPAM ─────────────────────────────────────────────
SPAM_MAX = 5
SPAM_WIN = 5
SPAM_CD = 300
FONT_SIZE = "1"

# ─── JSON ─────────────────────────────────────────────
def _lj(p, d):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return d

def _sj(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ─── STYLE ────────────────────────────────────────────
def _sty(text, color="#e8eaf6"):
    h = len(text.split("\n")[0]) + 1
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="font", size=FONT_SIZE, auto_format=False),
        MessageStyle(offset=0, length=h, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=h, style="bold", auto_format=False),
    ])

def sty_ok(t):
    return _sty(t, "#15A85F")

def sty_warn(t):
    return _sty(t, "#F7B503")

def sty_err(t):
    return _sty(t, "#DB342E")

def sty_info(t):
    return _sty(t, "#00BFFF")

def _reply(client, obj, tid, ttype, text, sty=sty_info, ttl=30000):
    msg = Message(text=text, style=sty(text))
    result = client.replyMessage(msg, obj, thread_id=tid, thread_type=ttype, ttl=ttl)
    if result and hasattr(result, 'msgId'):
        delay = get_delete_delay()
        if delay > 0:
            schedule_delete(client, result.msgId, tid, ttype)
    return result

# ─── CANVAS HELPERS ───────────────────────────────────
_FONTS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

def _font(size, bold=False):
    paths = [_FONTS[0], _FONTS[2]] if bold else [_FONTS[1], _FONTS[3]]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default(size=size)

def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _glow(img, cx, cy, r, col, a=18):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

def _grad_line(draw, x0, y, w, h, colors):
    seg = w // len(colors)
    for i, c in enumerate(colors):
        x1 = x0 + i * seg
        x2 = x0 + (i + 1) * seg if i < len(colors) - 1 else x0 + w
        draw.rectangle([x1, y, x2, y + h], fill=c)

# ─── CANVAS: STATS ────────────────────────────────────
def render_stats_card(bot_name, uid, prefix, version, author,
                      uptime, module_count, admin_count,
                      mute_count, ban_count, spam_count, warn_count):
    W, H = 780, 420
    BG = _hex("080b14")
    CARD = _hex("0d1220")
    BORDER = _hex("1a2035")
    AC = _hex("7c6aff")
    GR = _hex("15A85F")
    BL = _hex("4dabf7")
    YL = _hex("ffd43b")
    PU = _hex("cc5de8")
    RD = _hex("ff4466")
    TW = _hex("e8eaf6")
    TG = _hex("9aa0b8")
    TM = _hex("4a5570")

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for x in range(0, W, 36):
        for y in range(0, H, 36):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=_hex("141828"))

    for cx, cy, r, c in [(80, 80, 90, AC), (W - 80, H - 80, 80, _hex("ff6b9d")), (W // 2, H // 2, 60, GR)]:
        img = _glow(img, cx, cy, r, c, 15)
    draw = ImageDraw.Draw(img)

    PAD = 22
    HH = 120
    draw.rectangle([0, 0, W, HH], fill=_hex("09101e"))
    draw.rounded_rectangle([PAD, 16, PAD + 5, HH - 16], radius=3, fill=AC)
    draw.ellipse([PAD + 14, HH // 2 - 30, PAD + 54, HH // 2 + 30], fill=_hex("1a2a50"))
    draw.text((PAD + 16, HH // 2 - 20), "⚡", font=_font(32), fill=AC)
    draw.text((PAD + 68, 18), bot_name, font=_font(30, bold=True), fill=TW)
    draw.text((PAD + 68, 58), f"UID: {uid}  •  v{version}  •  by {author}", font=_font(13), fill=TG)
    draw.ellipse([PAD + 68, 86, PAD + 78, 96], fill=GR)
    draw.text((PAD + 84, 83), "Online", font=_font(12), fill=GR)
    draw.text((PAD + 140, 83), f"Uptime: {uptime}", font=_font(12), fill=TG)

    _grad_line(draw, 0, HH - 3, W, 3, [AC, _hex("9b59b6"), _hex("ff6b9d"), GR, BL])

    stats = [
        ("📦", "Modules", str(module_count), AC),
        ("🛡️", "Admins", str(admin_count), BL),
        ("⚡", "Prefix", f"'{prefix}'", YL),
        ("🔇", "Mute", str(mute_count), PU),
        ("🚫", "Ban", str(ban_count), RD),
        ("🛡", "Spam Block", str(spam_count), _hex("ffa94d")),
        ("⚠️", "Cảnh cáo", str(warn_count), YL),
        ("🔑", "Keys", "—", GR),
    ]
    SW = 168
    SH = 68
    sy = HH + 12
    per_row = 4
    for i, (icon, lbl, val, col) in enumerate(stats):
        ci = i % per_row
        ri = i // per_row
        bx = PAD + ci * (SW + 6)
        by = sy + ri * (SH + 8)
        draw.rounded_rectangle([bx, by, bx + SW, by + SH], radius=9, fill=CARD)
        draw.rounded_rectangle([bx, by, bx + SW, by + 3], radius=2, fill=col)
        draw.text((bx + 10, by + 10), icon, font=_font(16), fill=col)
        draw.text((bx + 36, by + 8), val, font=_font(18, bold=True), fill=col)
        draw.text((bx + 10, by + 42), lbl, font=_font(12), fill=TM)

    fy = H - 40
    draw.rectangle([0, fy, W, H], fill=_hex("09101e"))
    draw.line([0, fy, W, fy], fill=BORDER, width=1)
    draw.text((PAD, fy + 12), f"⚡ {bot_name}  •  LIGHT v{version}  •  prefix: {prefix}", font=_font(12), fill=TM)
    draw.text((W - PAD - 150, fy + 12), "powered by zlapi", font=_font(12), fill=TM)

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()

# ─── CANVAS: WARN CARD ────────────────────────────────
def render_warn_card(user_name, user_id, warn_count, max_warn, reason, admin_name):
    W, H = 620, 280
    BG = _hex("080b14")
    RD = _hex("ff4466")
    YL = _hex("ffd43b")
    TW = _hex("e8eaf6")
    TG = _hex("9aa0b8")
    TM = _hex("4a5570")
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for x in range(0, W, 36):
        for y in range(0, H, 36):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=_hex("141828"))
    img = _glow(img, W // 2, H // 2, 160, RD, 12)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 70], fill=_hex("1a0d0d"))
    draw.text((22, 14), "⚠️ CẢNH CÁO", font=_font(28, bold=True), fill=RD)
    draw.text((22, 50), f"Vi phạm bởi: {user_name}  •  ID: {user_id}", font=_font(13), fill=TG)
    _grad_line(draw, 0, 67, W, 3, [RD, YL, RD])

    draw.text((22, 84), f"📝 Lý do: {reason}", font=_font(16), fill=TW)
    draw.text((22, 116), f"🔧 Admin xử lý: {admin_name}", font=_font(14), fill=TG)

    bx, by = 22, 150
    bw = W - 44
    bh = 40
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8, fill=_hex("1a0d0d"))
    fill_w = int(bw * min(warn_count / max_warn, 1))
    if fill_w > 0:
        col = RD if warn_count >= max_warn else YL if warn_count >= max_warn // 2 else _hex("ffd43b")
        draw.rounded_rectangle([bx, by, bx + fill_w, by + bh], radius=8, fill=col)
    draw.text((bx + bw // 2 - 30, by + 10), f"{warn_count}/{max_warn} cảnh cáo", font=_font(14, bold=True), fill=TW)

    if warn_count >= max_warn:
        draw.text((22, 205), "🚨 ĐÃ ĐẠT GIỚI HẠN — SẼ BỊ XỬ LÝ!", font=_font(16, bold=True), fill=RD)
    else:
        remaining = max_warn - warn_count
        draw.text((22, 205), f"⚡ Còn {remaining} lần trước khi bị xử lý!", font=_font(15), fill=YL)

    draw.text((22, 240), f"⚡ Yuta Bot  •  Hệ thống cảnh cáo", font=_font(12), fill=TM)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()

# ─── CANVAS: BAN CARD ─────────────────────────────────
def render_ban_card(action, user_name, user_id, reason, admin_name, cmds="Tất cả"):
    W, H = 620, 260
    is_ban = action == "ban"
    AC = _hex("ff4466") if is_ban else _hex("15A85F")
    BG = _hex("080b14")
    TW = _hex("e8eaf6")
    TG = _hex("9aa0b8")
    TM = _hex("4a5570")
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for x in range(0, W, 36):
        for y in range(0, H, 36):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=_hex("141828"))
    img = _glow(img, W // 2, H // 2, 160, AC, 14)
    draw = ImageDraw.Draw(img)

    title = "🚫 BAN LỆNH" if is_ban else "✅ UNBAN LỆNH"
    draw.rectangle([0, 0, W, 68], fill=_hex("120808") if is_ban else _hex("081208"))
    draw.text((22, 12), title, font=_font(28, bold=True), fill=AC)
    draw.text((22, 50), f"Xử lý bởi: {admin_name}", font=_font(13), fill=TG)
    _grad_line(draw, 0, 65, W, 3, [AC, TM, AC])

    for i, (lbl, val) in enumerate([
        ("👤 Người dùng", user_name),
        ("🆔 User ID", str(user_id)),
        ("🎯 Lệnh", cmds),
        ("📝 Lý do", reason),
    ]):
        y = 82 + i * 40
        draw.text((22, y), lbl, font=_font(13, bold=True), fill=TM)
        draw.text((200, y), val, font=_font(14), fill=TW)

    draw.text((22, 232), f"⚡ Yuta Bot  •  Hệ thống quản lý lệnh", font=_font(12), fill=TM)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()

# ─── SEND IMAGE ───────────────────────────────────────
def _send_img(client, img_bytes, tid, ttype, caption=""):
    tmp = f"/tmp/canvas_{int(time.time())}.png"
    try:
        with open(tmp, "wb") as f:
            f.write(img_bytes)
        if hasattr(client, "sendLocalImage"):
            result = client.sendLocalImage(tmp, thread_id=tid, thread_type=ttype,
                                  message=Message(text=caption) if caption else None,
                                  ttl=180000)
            if result and hasattr(result, 'msgId'):
                delay = get_delete_delay()
                if delay > 0:
                    schedule_delete(client, result.msgId, tid, ttype)
        else:
            with open(tmp, "rb") as f:
                client.uploadAttachment([f], tid, ttype)
    except Exception as e:
        logger.error(f"[IMG] {e}")
    finally:
        try:
            os.remove(tmp)
        except:
            pass

# ─── SUB BOT MANAGER ──────────────────────────────────
class SubBotManager:
    _instances = {}

    @classmethod
    def start(cls, bot_id, bot_cfg):
        try:
            folder = bot_cfg.get("folder", "")
            script = os.path.join(folder, "run.py")
            if not os.path.exists(script):
                return False, "File không tồn tại"
            pid_f = os.path.join(folder, "bot.pid")
            if os.path.exists(pid_f):
                try:
                    with open(pid_f) as f:
                        os.kill(int(f.read()), signal.SIGTERM)
                except:
                    pass
                os.remove(pid_f)
            proc = subprocess.Popen([sys.executable, script], cwd=folder,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    start_new_session=True)
            cls._instances[str(bot_id)] = {"proc": proc, "cfg": bot_cfg}
            with open(pid_f, "w") as f:
                f.write(str(proc.pid))
            return True, proc.pid
        except Exception as e:
            return False, str(e)

    @classmethod
    def stop(cls, bot_id):
        try:
            info = cls._instances.pop(str(bot_id), None)
            if info and info.get("proc"):
                info["proc"].terminate()
            pid_f = os.path.join(info["cfg"]["folder"], "bot.pid") if info else ""
            if os.path.exists(pid_f):
                try:
                    with open(pid_f) as f:
                        os.kill(int(f.read()), signal.SIGTERM)
                except:
                    pass
                os.remove(pid_f)
            return True
        except:
            return False

    @classmethod
    def is_running(cls, bot_id):
        info = cls._instances.get(str(bot_id))
        if info and info.get("proc"):
            return info["proc"].poll() is None
        return False

# ─── DEFAULT NS ───────────────────────────────────────
DEFAULT_NS = {
    "name": "Vandat Bot",
    "description": "Bot hỗ trợ Zalo",
    "version": "1.0.0",
    "author": "Admin",
    "welcome": "Xin chào! Tôi là {name}, gõ {prefix}menu để xem lệnh.",
    "goodbye": "Tạm biệt!",
    "error_msg": "❌ Lỗi, thử lại sau!",
}
MAX_WARN = 3

class BlockedCommandStub:
    def is_command_blocked(self, command, author_id, thread_id):
        return False

# ══════════════════════════════════════════════════════
#  MAIN BOT
# ══════════════════════════════════════════════════════
class MainBot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.settings = {"prefix": PREFIX}
        self.ADMIN = str(ADMIN)
        self.ADM = []
        self.duyetbox_data = {}
        self.bcmd_handler = BlockedCommandStub()
        self.uid = None
        self._start_time = time.time()

        self._notify = _lj(NOTIFY_FILE, {})
        self._notify_admin = _lj(NOTIFY_ADM_FILE, {"enabled": True})["enabled"]
        self._ns = {**DEFAULT_NS, **_lj(NS_FILE, {})}
        self._muted = _lj(MUTE_FILE, {})
        self._approve = _lj(APPROVE_FILE, [])
        self._spam_blocked = _lj(SPAM_FILE, {})
        self._warnings = _lj(WARN_FILE, {})
        self._spam_counter = defaultdict(list)
        self._spam_lock = threading.Lock()
        self._bot_enabled = True

        try:
            info = self.fetchAccountInfo()
            self.uid = info.profile.get("userId")
        except Exception as e:
            logger.error(f"Không lấy được UID: {e}")
            raise
        if not self.uid:
            raise RuntimeError("Không xác định được UID bot.")

        self.command_handler = CommandHandler(self)
        logger.info(f"✅ [{self.ns('name')}] UID: {self.uid}")

    def ns(self, key, fb=""):
        v = self._ns.get(key, fb)
        return v.replace("{name}", self._ns.get("name", "Bot")) \
                .replace("{prefix}", self.settings.get("prefix", PREFIX)) \
                .replace("{version}", self._ns.get("version", "1.0.0")) \
                .replace("{author}", self._ns.get("author", "Admin"))

    def ns_set(self, k, v):
        self._ns[k] = v
        _sj(NS_FILE, self._ns)

    def ns_reset(self):
        self._ns = dict(DEFAULT_NS)
        _sj(NS_FILE, self._ns)

    def is_notify_on(self, tid):
        return self._notify.get(str(tid), True)

    def set_notify(self, tid, s):
        self._notify[str(tid)] = s
        _sj(NOTIFY_FILE, self._notify)

    def is_notify_admin_on(self):
        return self._notify_admin

    def set_notify_admin(self, s):
        self._notify_admin = s
        _sj(NOTIFY_ADM_FILE, {"enabled": s})

    def is_muted(self, uid, tid):
        k = f"{uid}_{tid}"
        info = self._muted.get(k)
        if not info:
            return False
        until = info.get("until")
        if until and time.time() > until:
            del self._muted[k]
            _sj(MUTE_FILE, self._muted)
            return False
        return True

    def add_warning(self, uid):
        uid = str(uid)
        self._warnings[uid] = self._warnings.get(uid, 0) + 1
        _sj(WARN_FILE, self._warnings)
        return self._warnings[uid]

    def clear_warning(self, uid):
        self._warnings.pop(str(uid), None)
        _sj(WARN_FILE, self._warnings)

    def get_warning(self, uid):
        return self._warnings.get(str(uid), 0)

    def _check_spam(self, uid, tid):
        uid = str(uid)
        now = time.time()
        until = self._spam_blocked.get(uid)
        if until:
            if now < until:
                return True
            del self._spam_blocked[uid]
            _sj(SPAM_FILE, self._spam_blocked)
        with self._spam_lock:
            ts = [t for t in self._spam_counter[uid] if now - t < SPAM_WIN]
            ts.append(now)
            self._spam_counter[uid] = ts
            if len(ts) >= SPAM_MAX:
                self._spam_counter[uid] = []
                self._spam_blocked[uid] = now + SPAM_CD
                _sj(SPAM_FILE, self._spam_blocked)
                return True
        return False

    def _punish_spammer(self, uid, tid, ttype, mid, msg_obj):
        uid = str(uid)
        try:
            self.deleteGroupMsg(mid, uid, tid)
        except:
            pass
        if ttype == ThreadType.GROUP:
            try:
                self.kickUser(uid, tid)
                logger.info(f"🦶 Kicked {uid}")
            except:
                self._spam_blocked[uid] = time.time() + SPAM_CD
                _sj(SPAM_FILE, self._spam_blocked)

    def _uptime_str(self):
        s = int(time.time() - self._start_time)
        h, m = divmod(s // 60, 60)
        d, h = divmod(h, 24)
        return f"{d}d {h}h {m}m" if d else f"{h}h {m}m"

    def DNgoc(self):
        try:
            with open("asset/seting.json", "r", encoding="utf-8") as f:
                d = json.load(f)
            s = {str(x) for x in d.get("adm", [])}
            s.add(str(d.get("admin", "")))
            return s
        except:
            return {self.ADMIN}

    # ══════════════════════════════════════════════════
    #  LỆNH: BOT ON/OFF
    # ══════════════════════════════════════════════════
    def _handle_botonoff_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        arg = msg.strip()[len(p):].strip().lower()

        if arg == "bot on":
            self._bot_enabled = True
            _reply(self, obj, tid, ttype, "SUCCESS\n    🟢 Bot đã bật toàn cục!", sty_ok)
        elif arg == "bot off":
            self._bot_enabled = False
            _reply(self, obj, tid, ttype, "SUCCESS\n    🔴 Bot đã tắt toàn cục!", sty_ok)
        elif arg == "bot on all":
            self._notify.clear()
            _sj(NOTIFY_FILE, self._notify)
            self._bot_enabled = True
            _reply(self, obj, tid, ttype, "SUCCESS\n    🟢 Bot bật ở tất cả nhóm!", sty_ok)
        elif arg == "bot off all":
            for t in list(self._notify.keys()):
                self._notify[t] = False
            _sj(NOTIFY_FILE, self._notify)
            self._bot_enabled = False
            _reply(self, obj, tid, ttype, "SUCCESS\n    🔴 Bot tắt ở tất cả nhóm!", sty_ok)
        elif arg in ("bot on here", "bot on nhóm"):
            self.set_notify(str(tid), True)
            _reply(self, obj, tid, ttype, "SUCCESS\n    🟢 Bot bật ở nhóm này!", sty_ok)
        elif arg in ("bot off here", "bot off nhóm"):
            self.set_notify(str(tid), False)
            _reply(self, obj, tid, ttype, "SUCCESS\n    🔴 Bot tắt ở nhóm này!", sty_ok)
        elif arg == "bot status":
            global_st = "🟢 BẬT" if self._bot_enabled else "🔴 TẮT"
            here_st = "🟢 BẬT" if self.is_notify_on(str(tid)) else "🔴 TẮT"
            off_count = sum(1 for v in self._notify.values() if not v)
            _reply(self, obj, tid, ttype,
                   f"INFO\n"
                   f"    Toàn cục   : {global_st}\n"
                   f"    Nhóm này   : {here_st}\n"
                   f"    Nhóm tắt   : {off_count}\n"
                   f"    {p}bot on/off\n"
                   f"    {p}bot on/off all\n"
                   f"    {p}bot on/off here", sty_info, ttl=60000)

    # ══════════════════════════════════════════════════
    #  LỆNH: STATS
    # ══════════════════════════════════════════════════
    def _handle_stats_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return

        def _run():
            try:
                img = render_stats_card(
                    bot_name=self.ns("name"),
                    uid=str(self.uid),
                    prefix=self.settings.get("prefix", PREFIX),
                    version=self.ns("version"),
                    author=self.ns("author"),
                    uptime=self._uptime_str(),
                    module_count=len(self.command_handler.LIGHT),
                    admin_count=len(self.DNgoc()),
                    mute_count=len(self._muted),
                    ban_count=len(self._spam_blocked),
                    spam_count=sum(1 for v in self._spam_blocked.values() if v > time.time()),
                    warn_count=sum(self._warnings.values()),
                )
                _send_img(self, img, tid, ttype)
            except Exception as e:
                _reply(self, obj, tid, ttype,
                       f"STATS\n"
                       f"    ⚡ Bot  : {self.ns('name')}\n"
                       f"    🕐 Up   : {self._uptime_str()}\n"
                       f"    📦 Mods : {len(self.command_handler.LIGHT)}\n"
                       f"    🔇 Mute : {len(self._muted)}\n"
                       f"    ⚠️ Warn : {sum(self._warnings.values())}", sty_info)

        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════
    #  LỆNH: WARN
    # ══════════════════════════════════════════════════
    def _handle_warn_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        body = msg.strip()[len(p + "warn"):].strip()
        args = body.split(None, 1)
        sub = args[0].lower() if args else ""

        if sub == "list":
            if not self._warnings:
                _reply(self, obj, tid, ttype, "INFO\n    Không có ai bị cảnh cáo.", sty_info)
                return
            lines = ["⚠️ WARN LIST"]
            for u, c in self._warnings.items():
                lines.append(f"    • {u}: {c}/{MAX_WARN}")
            _reply(self, obj, tid, ttype, "\n".join(lines), sty_warn, ttl=60000)
            return

        if sub == "clear":
            target = args[1].strip() if len(args) > 1 else ""
            if target:
                self.clear_warning(target)
                _reply(self, obj, tid, ttype, f"SUCCESS\n    ✅ Xoá cảnh cáo {target}", sty_ok)
            else:
                self._warnings.clear()
                _sj(WARN_FILE, self._warnings)
                _reply(self, obj, tid, ttype, "SUCCESS\n    ✅ Đã xoá tất cả cảnh cáo", sty_ok)
            return

        if not sub:
            _reply(self, obj, tid, ttype,
                   f"INFO\n    {p}warn <uid> [lý do]\n    {p}warn list\n    {p}warn clear [uid]", sty_info)
            return

        target = sub
        reason = args[1].strip() if len(args) > 1 else "Vi phạm nội quy"
        count = self.add_warning(target)
        name = target
        try:
            name = self.fetchUserInfo(target).changed_profiles.get(str(target), {}).get("displayName", target)
        except:
            pass
        admin_name = uid
        try:
            admin_name = self.fetchUserInfo(uid).changed_profiles.get(str(uid), {}).get("displayName", uid)
        except:
            pass

        def _run():
            try:
                img = render_warn_card(name, target, count, MAX_WARN, reason, admin_name)
                _send_img(self, img, tid, ttype)
            except:
                _reply(self, obj, tid, ttype,
                       f"WARNING\n    ⚠️ Cảnh cáo {name}\n    📝 {reason}\n    {count}/{MAX_WARN}", sty_warn)
            if count >= MAX_WARN and ttype == ThreadType.GROUP:
                try:
                    self.kickUser(target, tid)
                    _reply(self, obj, tid, ttype, f"SUCCESS\n    🦶 {name} đã bị kick do {MAX_WARN} lần cảnh cáo!", sty_err)
                    self.clear_warning(target)
                except:
                    pass

        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════
    #  LỆNH: BAN/UNBAN
    # ══════════════════════════════════════════════════
    def _handle_ban_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        is_unban = msg.strip().lower().startswith(p + "unban")
        body = msg.strip()[len(p + ("unban" if is_unban else "ban")):].strip()
        args = body.split(None, 2)
        target = args[0] if args else ""
        if not target:
            _reply(self, obj, tid, ttype,
                   f"INFO\n    {p}ban <uid> [lệnh1,lệnh2] [lý do]\n    {p}unban <uid>", sty_info)
            return
        cmds_raw = args[1] if len(args) > 1 else "all"
        reason = args[2] if len(args) > 2 else "Không có lý do"
        name = target
        try:
            name = self.fetchUserInfo(target).changed_profiles.get(str(target), {}).get("displayName", target)
        except:
            pass
        admin_name = uid
        try:
            admin_name = self.fetchUserInfo(uid).changed_profiles.get(str(uid), {}).get("displayName", uid)
        except:
            pass

        BANNED_F = "modules/cache/banned_users.json"
        banned = _lj(BANNED_F, {})
        if is_unban:
            banned.pop(str(target), None)
            _sj(BANNED_F, banned)
            action = "unban"
        else:
            ban_cmds = [] if cmds_raw.lower() == "all" else [c.strip() for c in cmds_raw.split(",")]
            banned[str(target)] = {"cmds": ban_cmds, "reason": reason, "by": str(uid), "at": datetime.now().strftime("%d/%m/%Y %H:%M")}
            _sj(BANNED_F, banned)
            action = "ban"

        def _run():
            try:
                img = render_ban_card(action, name, target, reason, admin_name,
                                      "Tất cả lệnh" if not ban_cmds else cmds_raw if not is_unban else "—")
                _send_img(self, img, tid, ttype)
            except:
                _reply(self, obj, tid, ttype,
                       f"{'SUCCESS' if is_unban else 'WARNING'}\n    {'✅ UNBAN' if is_unban else '🚫 BAN'} {name}\n    Lý do: {reason}",
                       sty_ok if is_unban else sty_err)

        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════
    #  LỆNH: KICK
    # ══════════════════════════════════════════════════
    def _handle_kick_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        body = msg.strip()[len(p + "kick"):].strip().split()
        if not body:
            _reply(self, obj, tid, ttype, f"WARNING\n    {p}kick <uid>", sty_warn)
            return
        target = body[0]
        reason = " ".join(body[1:]) if len(body) > 1 else "Admin xử lý"
        try:
            self.kickUser(target, tid)
            name = target
            try:
                name = self.fetchUserInfo(target).changed_profiles.get(str(target), {}).get("displayName", target)
            except:
                pass
            _reply(self, obj, tid, ttype, f"SUCCESS\n    🦶 Đã kick {name}\n    📝 Lý do: {reason}", sty_ok)
        except Exception as e:
            _reply(self, obj, tid, ttype, f"ERROR\n    Không kick được: {e}", sty_err)

    # ══════════════════════════════════════════════════
    #  LỆNH: MUTE
    # ══════════════════════════════════════════════════
    def _handle_mute_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        args = msg.strip()[len(p + "mute"):].strip().split()
        if not args:
            _reply(self, obj, tid, ttype,
                   f"INFO\n    {p}mute <uid> [phút] [lý do]\n    {p}mute unmute <uid>\n    {p}mute list", sty_info)
            return
        sub = args[0].lower()
        if sub == "unmute":
            uid2 = args[1] if len(args) > 1 else ""
            if not uid2:
                _reply(self, obj, tid, ttype, f"WARNING\n    {p}mute unmute <uid>", sty_warn)
                return
            k = f"{uid2}_{tid}"
            if k in self._muted:
                del self._muted[k]
                _sj(MUTE_FILE, self._muted)
            _reply(self, obj, tid, ttype, f"SUCCESS\n    🔊 Đã unmute {uid2}", sty_ok)
            return
        if sub == "list":
            if not self._muted:
                _reply(self, obj, tid, ttype, "INFO\n    Không có ai bị mute.", sty_info)
                return
            lines = ["🔇 MUTE LIST"]
            for k, v in self._muted.items():
                u, _ = k.rsplit("_", 1)
                until = v.get("until")
                t_str = datetime.fromtimestamp(until).strftime("%H:%M %d/%m") if until else "Vĩnh viễn"
                lines.append(f"    • {u} | {t_str} | {v.get('reason', '?')}")
            _reply(self, obj, tid, ttype, "\n".join(lines), sty_info, ttl=60000)
            return
        uid2 = sub
        mins = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        reason = " ".join(args[2:]) if len(args) > 2 else "Không có lý do"
        k = f"{uid2}_{tid}"
        self._muted[k] = {"until": time.time() + mins * 60 if mins else None, "reason": reason, "by": str(uid), "at": datetime.now().strftime("%d/%m/%Y %H:%M")}
        _sj(MUTE_FILE, self._muted)
        _reply(self, obj, tid, ttype, f"SUCCESS\n    🔇 Mute {uid2}\n    ⏱️ {'Vĩnh viễn' if not mins else str(mins) + ' phút'}\n    📝 {reason}", sty_ok)

    # ══════════════════════════════════════════════════
    #  LỆNH: APPROVE
    # ══════════════════════════════════════════════════
    def _handle_approve_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        arg = msg.strip()[len(p + "approve"):].strip().lower()
        if arg in ("on", "bật", "bat"):
            if str(tid) not in self._approve:
                self._approve.append(str(tid))
                _sj(APPROVE_FILE, self._approve)
            _reply(self, obj, tid, ttype, "SUCCESS\n    ✅ Bật auto duyệt thành viên.", sty_ok)
        elif arg in ("off", "tắt", "tat"):
            if str(tid) in self._approve:
                self._approve.remove(str(tid))
                _sj(APPROVE_FILE, self._approve)
            _reply(self, obj, tid, ttype, "SUCCESS\n    🔴 Tắt auto duyệt.", sty_ok)
        else:
            state = "BẬT ✅" if str(tid) in self._approve else "TẮT 🔴"
            _reply(self, obj, tid, ttype, f"INFO\n    Auto approve: {state}\n    {p}approve on/off", sty_info)

    # ══════════════════════════════════════════════════
    #  LỆNH: NS
    # ══════════════════════════════════════════════════
    def _handle_ns_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        body = msg.strip()[len(p + "ns"):].strip()
        args = body.split(None, 1)
        sub = args[0].lower() if args else ""
        val = args[1].strip() if len(args) > 1 else ""
        if sub in ("", "list"):
            lines = ["NAMESERVER"] + [f"    {k}: {v}" for k, v in self._ns.items()]
            lines += [f"    ────────────", f"    {p}ns set <key> <value>", f"    {p}ns reset"]
            _reply(self, obj, tid, ttype, "\n".join(lines), sty_info, ttl=60000)
        elif sub == "set":
            kv = val.split(None, 1)
            if len(kv) < 2:
                _reply(self, obj, tid, ttype, f"WARNING\n    {p}ns set <key> <value>", sty_warn)
                return
            self.ns_set(kv[0].lower(), kv[1])
            _reply(self, obj, tid, ttype, f"SUCCESS\n    {kv[0]} → {kv[1]}", sty_ok)
        elif sub == "reset":
            self.ns_reset()
            _reply(self, obj, tid, ttype, "SUCCESS\n    ♻️ Reset nameserver.", sty_ok)
        else:
            _reply(self, obj, tid, ttype, f"INFO\n    {p}ns [list|set|reset]", sty_info)

    # ══════════════════════════════════════════════════
    #  LỆNH: NOTIFY
    # ══════════════════════════════════════════════════
    def _handle_notify_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        arg = msg.strip()[len(p + "notify"):].strip().lower()
        acts = {"on": ("n", True), "bật": ("n", True), "bat": ("n", True),
                "off": ("n", False), "tắt": ("n", False), "tat": ("n", False),
                "adminon": ("a", True), "adminoff": ("a", False),
                "allon": ("all", True), "alloff": ("all", False)}
        if arg in acts:
            sc, st = acts[arg]
            if sc == "n":
                self.set_notify(str(tid), st)
            elif sc == "a":
                self.set_notify_admin(st)
            elif sc == "all":
                if st:
                    self._notify.clear()
                else:
                    for t in list(self._notify.keys()):
                        self._notify[t] = False
                _sj(NOTIFY_FILE, self._notify)
            _reply(self, obj, tid, ttype, f"SUCCESS\n    {'BẬT 🔔' if st else 'TẮT 🔕'}", sty_ok)
        else:
            s1 = "BẬT 🔔" if self.is_notify_on(str(tid)) else "TẮT 🔕"
            s2 = "BẬT 🔔" if self.is_notify_admin_on() else "TẮT 🔕"
            off = sum(1 for v in self._notify.values() if not v)
            _reply(self, obj, tid, ttype,
                   f"INFO\n    Bot nhóm này: {s1}\n    Notify admin: {s2}\n    Nhóm tắt: {off}\n"
                   f"    ────────────────\n    {p}notify on/off\n    {p}notify adminon/adminoff\n    {p}notify allon/alloff",
                   sty_info, ttl=60000)

    # ══════════════════════════════════════════════════
    #  LỆNH: SPAM
    # ══════════════════════════════════════════════════
    def _handle_spam_cmd(self, msg, obj, tid, ttype, uid):
        if not check_is_admin(uid):
            _reply(self, obj, tid, ttype, "ERROR\n    Chỉ admin dùng được!", sty_err)
            return
        p = self.settings.get("prefix", PREFIX)
        args = msg.strip()[len(p + "spam"):].strip().split()
        sub = args[0].lower() if args else ""
        if sub == "list":
            now = time.time()
            active = {u: v for u, v in self._spam_blocked.items() if v > now}
            if not active:
                _reply(self, obj, tid, ttype, "INFO\n    Blacklist trống.", sty_info)
                return
            lines = [f"SPAM BLACKLIST ({len(active)})"] + [f"    • {u} — {datetime.fromtimestamp(v).strftime('%H:%M %d/%m')}" for u, v in active.items()]
            _reply(self, obj, tid, ttype, "\n".join(lines), sty_warn, ttl=60000)
        elif sub == "clear":
            uid2 = args[1] if len(args) > 1 else ""
            if uid2:
                self._spam_blocked.pop(uid2, None)
            else:
                self._spam_blocked.clear()
            _sj(SPAM_FILE, self._spam_blocked)
            _reply(self, obj, tid, ttype, "SUCCESS\n    ✅ Đã xoá blacklist spam.", sty_ok)
        else:
            _reply(self, obj, tid, ttype, f"INFO\n    {p}spam list/clear [uid]", sty_info)

    # ══════════════════════════════════════════════════
    #  NOTIFY ADMIN
    # ══════════════════════════════════════════════════
    def send_notification_to_admin(self, author_id, message_content, thread_id, thread_type):
        if not self.is_notify_admin_on():
            return
        try:
            admin_ids = self.DNgoc()
            if not admin_ids:
                return
            info = self.fetchUserInfo(author_id)
            profile = info.changed_profiles.get(str(author_id), {})
            dname = profile.get("displayName", "Unknown")
            uname = profile.get("username", "Unknown")
            grp = ""
            if thread_type == ThreadType.GROUP:
                try:
                    grp = self.fetchGroupInfo(thread_id).gridInfoMap.get(str(thread_id), {}).get("name", "?")
                except:
                    grp = "?"
            try:
                qr = self.getQRLink(author_id).get(str(author_id), {}).get("qrUrl", "")
            except:
                qr = ""
            avt = profile.get("avatar", "")
            header = f"NEW MESSAGE [{self.ns('name')}]"
            body = (f"{header}\n\n    Name: {dname}\n    UID: {author_id}\n    Username: {uname}\n" +
                    (f"    Group: {grp}\n" if grp else "") +
                    f"    Time: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
                    f"    Msg: {message_content[:200]}\n\n    Avatar: {avt}\n    QR: {qr}\n")
            hl = len(header) + 1
            style = MultiMsgStyle([
                MessageStyle(offset=0, length=len(body), style="font", size=FONT_SIZE, auto_format=False),
                MessageStyle(offset=0, length=hl, style="bold", auto_format=False),
                MessageStyle(offset=0, length=hl, style="color", color="#15A85F", auto_format=False),
            ])
            msg = Message(text=body, style=style)
            for aid in admin_ids:
                try:
                    self.sendMessage(msg, aid, ThreadType.USER)
                    if qr:
                        try:
                            self.sendBusinessCard(author_id, qr, aid, ThreadType.USER)
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            print(f"Notify admin lỗi: {e}")

    # ══════════════════════════════════════════════════
    #  ON EVENT
    # ══════════════════════════════════════════════════
    def onEvent(self, event_data, event_type):
        try:
            if hasattr(event_data, "updateType") and event_data.updateType in (10, 11):
                tid = str(getattr(event_data, "groupId", ""))
                if tid in self._approve:
                    for m in getattr(event_data, "members", []):
                        u = str(getattr(m, "userId", getattr(m, "id", "")))
                        if u:
                            try:
                                self.acceptUserIntoGroup(u, tid)
                            except:
                                pass
            if hasattr(event_data, "updateType") and event_data.updateType in (6, 7):
                tid = str(getattr(event_data, "groupId", ""))
                if tid in self._welcome:
                    for m in getattr(event_data, "members", []):
                        u = str(getattr(m, "userId", getattr(m, "id", "")))
                        if u:
                            try:
                                name = self.fetchUserInfo(u).changed_profiles.get(u, {}).get("displayName", u)
                                txt = self._welcome[tid].replace("{name}", name).replace("{uid}", u)
                                style = MultiMsgStyle([MessageStyle(offset=0, length=len(txt), style="font", size=FONT_SIZE, auto_format=False)])
                                self.send(Message(text=txt, style=style), tid, ThreadType.GROUP, ttl=60000)
                            except:
                                pass
        except:
            pass

    # ══════════════════════════════════════════════════
    #  ON MESSAGE
    # ══════════════════════════════════════════════════
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        update_activity()

        if is_sleeping():
            try:
                c = message_object.content
                if isinstance(c, str):
                    msg_text = c.lower()
                elif isinstance(c, dict) and "title" in c:
                    msg_text = c["title"].lower()
                else:
                    msg_text = ""

                if "kryzis" in msg_text:
                    wake_up()
                    self.send(Message(text="Kryzis nghe", style=_sty("Kryzis nghe")), thread_id, thread_type, ttl=60000)
                    return
            except:
                pass
            return

        try:
            if message_object.msgType == "chat.sticker":
                return
            c = message_object.content
            if isinstance(c, dict) and "title" in c:
                message_text = c["title"]
            elif isinstance(c, str):
                message_text = c
            elif isinstance(c, dict) and "href" in c:
                message_text = c["href"]
            else:
                return
        except:
            return

        if not message_text or not message_text.strip():
            return

        # Kiểm tra từ khóa kw
        kw_on_message(message_text, message_object, thread_id, thread_type, self)

        if message_text.strip().isdigit():
            if handle_skin_choice(message_text.strip(), message_object, thread_id, thread_type, author_id, self):
                return
            if author_id in scl_user_states:
                scl_handle_message(message_text, message_object, thread_id, thread_type, author_id, self)
                return

        prefix = self.settings.get("prefix", PREFIX)
        is_admin = check_is_admin(author_id)

        if not self._bot_enabled and not is_admin:
            return

        if not is_admin and self.is_muted(str(author_id), str(thread_id)):
            try:
                self.deleteGroupMsg(mid, author_id, thread_id)
            except:
                pass
            return

        if not is_admin and message_text.strip().startswith(prefix):
            if self._check_spam(str(author_id), str(thread_id)):
                self._punish_spammer(author_id, thread_id, thread_type, mid, message_object)
                return

        specials = {
            prefix + "notify": self._handle_notify_cmd,
            prefix + "approve": self._handle_approve_cmd,
            prefix + "kick": self._handle_kick_cmd,
            prefix + "warn": self._handle_warn_cmd,
            prefix + "ban": self._handle_ban_cmd,
            prefix + "unban": self._handle_ban_cmd,
            prefix + "spam": self._handle_spam_cmd,
        }

        for trigger, handler in specials.items():
            if message_text.strip().startswith(trigger) and (
                len(message_text.strip()) == len(trigger) or
                message_text.strip()[len(trigger)] in (" ", "\n")
            ):
                handler(message_text, message_object, thread_id, thread_type, author_id)
                return

        if not self.is_notify_on(str(thread_id)) and not is_admin:
            return

        self.command_handler.handle_command(
            message_text, author_id, message_object, thread_id, thread_type)


# ══════════════════════════════════════════════════════
#  START
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    if os.path.exists("session.json"):
        try:
            os.remove("session.json")
            logger.warning("Xoá session.json cũ.")
        except:
            pass
    try:
        client = MainBot(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
        send_reset_success_message(client)
        client.listen()
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        traceback.print_exc()
        sys.exit(1)


def _create_bot_folder_stub(bot_id, bot_name, bot_prefix, admin_id, bot_imei, bot_cookies):
    folder = os.path.join(BOTS_DIR, bot_name)
    os.makedirs(folder, exist_ok=True)
    cfg = {"IMEI": bot_imei, "SESSION_COOKIES": bot_cookies, "PREFIX": bot_prefix, "ADMIN": admin_id}
    _sj(os.path.join(folder, "bot_config.json"), cfg)
    return folder


SubBotManager.create_bot_folder = staticmethod(_create_bot_folder_stub)