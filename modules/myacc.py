import os
import json
import requests
import threading
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.0',
    'credits': 'Yuta Bot',
    'description': 'Quản lý tài khoản bot',
    'power': 'Admin'
}

AVATAR_HISTORY_FILE = "modules/cache/avatar_history.json"
MAX_AVATAR_HISTORY  = 20

# ─── HELPERS ─────────────────────────────────────────────────────
def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _is_admin(author_id):
    """Dùng check_is_admin từ LIGHT.py nếu có, fallback đọc seting.json trực tiếp."""
    try:
        from LIGHT import check_is_admin
        return check_is_admin(author_id)
    except Exception:
        pass
    try:
        with open("asset/seting.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        owner  = str(data.get("admin", ""))
        admins = [str(x) for x in data.get("adm", [])]
        return str(author_id) == owner or str(author_id) in admins
    except Exception:
        return False

def _reply(client, text, message_object, thread_id, thread_type, bold_len=0):
    styles = []
    if bold_len:
        styles = [
            MessageStyle(offset=0, length=bold_len, style="bold", auto_format=False),
            MessageStyle(offset=0, length=10000,     style="font", size="8", auto_format=False),
        ]
    client.replyMessage(
        Message(text=text, style=MultiMsgStyle(styles) if styles else None),
        message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
    )

def _get_profile(client):
    try:
        info = client.fetchAccountInfo()
        return info.profile if hasattr(info, "profile") else {}
    except Exception:
        return {}

def _load_history():
    return _load_json(AVATAR_HISTORY_FILE, [])

def _push_history(url: str, note: str = ""):
    history = _load_history()
    if history and history[0].get("url") == url:
        return
    history.insert(0, {
        "url":  url,
        "note": note,
        "at":   datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    _save_json(AVATAR_HISTORY_FILE, history[:MAX_AVATAR_HISTORY])

def _download_image(url: str):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        path = f"/tmp/myacc_avt_{int(datetime.now().timestamp())}.jpg"
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except Exception:
        return None

# ─── HANDLER ─────────────────────────────────────────────────────
def handle_myacc(message, message_object, thread_id, thread_type, author_id, client):
    if not _is_admin(author_id):
        _reply(client, "🚫 Chỉ admin mới dùng được lệnh này.",
               message_object, thread_id, thread_type)
        return

    prefix = client.settings.get("prefix", "")
    cmd    = prefix + "myacc"
    body   = message.strip()[len(cmd):].strip()
    args   = body.split(None, 1)
    sub    = args[0].lower() if args else ""
    val    = args[1].strip() if len(args) > 1 else ""

    # ── INFO ─────────────────────────────────────────────────
    if sub == "":
        p = _get_profile(client)
        uid  = str(getattr(client, "uid", "?"))
        name = p.get("displayName") or p.get("zaloName") or "?"
        dob  = p.get("dob", "?")
        bio  = p.get("sdesc") or p.get("status") or "?"
        avt  = p.get("avatar", "?")
        hist = _load_history()

        text = (
            f"👤 TÀI KHOẢN BOT\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📛 Tên      : {name}\n"
            f"🆔 UID      : {uid}\n"
            f"🎂 Ngày sinh: {dob}\n"
            f"📝 Bio      : {bio}\n"
            f"🖼️ Avatar   : {avt[:60]}{'...' if len(avt)>60 else ''}\n"
            f"📸 Lịch sử  : {len(hist)} ảnh\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  {cmd} name <tên>       — đổi tên\n"
            f"  {cmd} dob <dd/mm/yyyy> — đổi ngày sinh\n"
            f"  {cmd} bio <nội dung>   — đổi bio\n"
            f"  {cmd} avt              — đổi avatar (reply ảnh)\n"
            f"  {cmd} avatarOld        — xem avatar cũ\n"
            f"  {cmd} avatarOld <số>   — set lại avatar cũ"
        )
        _reply(client, text, message_object, thread_id, thread_type, bold_len=16)

    # ── ĐỔI TÊN ──────────────────────────────────────────────
    elif sub == "name":
        if not val:
            _reply(client, f"📋 Dùng: {cmd} name <tên mới>",
                   message_object, thread_id, thread_type)
            return
        try:
            client.changeAccountName(val)
            _reply(client, f"✅ Đã đổi tên thành: {val}",
                   message_object, thread_id, thread_type)
        except Exception as e:
            _reply(client, f"❌ Lỗi đổi tên: {e}",
                   message_object, thread_id, thread_type)

    # ── ĐỔI DOB ──────────────────────────────────────────────
    elif sub == "dob":
        if not val:
            _reply(client, f"📋 Dùng: {cmd} dob <dd/mm/yyyy>\nVí dụ: {cmd} dob 01/01/2000",
                   message_object, thread_id, thread_type)
            return
        try:
            datetime.strptime(val, "%d/%m/%Y")
            client.changeAccountDOB(val)
            _reply(client, f"✅ Đã đổi ngày sinh thành: {val}",
                   message_object, thread_id, thread_type)
        except ValueError:
            _reply(client, "❌ Định dạng sai. Dùng: dd/mm/yyyy",
                   message_object, thread_id, thread_type)
        except Exception as e:
            _reply(client, f"❌ Lỗi: {e}", message_object, thread_id, thread_type)

    # ── ĐỔI BIO ──────────────────────────────────────────────
    elif sub == "bio":
        if not val:
            _reply(client, f"📋 Dùng: {cmd} bio <nội dung>",
                   message_object, thread_id, thread_type)
            return
        try:
            client.changeAccountInfo(key="sdesc", value=val)
            _reply(client, f"✅ Đã đổi bio:\n{val}",
                   message_object, thread_id, thread_type)
        except Exception as e:
            _reply(client, f"❌ Lỗi: {e}", message_object, thread_id, thread_type)

    # ── ĐỔI AVATAR ───────────────────────────────────────────
    elif sub == "avt":
        img_url = None
        try:
            ref = getattr(message_object, "referenceMsgContent", None) or \
                  getattr(message_object, "replyMsg", None)
            if ref:
                c = getattr(ref, "content", {})
                if isinstance(c, dict):
                    img_url = c.get("href") or c.get("normalUrl") or c.get("hdUrl")
            if not img_url:
                c = getattr(message_object, "content", {})
                if isinstance(c, dict):
                    img_url = c.get("href") or c.get("normalUrl") or c.get("hdUrl")
        except Exception:
            pass

        if not img_url:
            _reply(client,
                   f"📋 Reply vào 1 ảnh rồi gõ:\n  {cmd} avt",
                   message_object, thread_id, thread_type)
            return

        _reply(client, "⏳ Đang đổi avatar...", message_object, thread_id, thread_type)

        def _do():
            try:
                p = _get_profile(client)
                old = p.get("avatar", "")
                if old:
                    _push_history(old, "trước khi đổi")
                tmp = _download_image(img_url)
                if not tmp:
                    _reply(client, "❌ Không tải được ảnh.", message_object, thread_id, thread_type)
                    return
                client.changeAccountAvatar(tmp)
                _push_history(img_url, "đã set")
                try: os.remove(tmp)
                except: pass
                _reply(client, "✅ Đổi avatar thành công!", message_object, thread_id, thread_type)
            except Exception as e:
                _reply(client, f"❌ Lỗi: {e}", message_object, thread_id, thread_type)

        threading.Thread(target=_do, daemon=True).start()

    # ── AVATAR CŨ ────────────────────────────────────────────
    elif sub == "avatarold":
        history = _load_history()

        if not history:
            _reply(client, "📭 Chưa có lịch sử avatar.",
                   message_object, thread_id, thread_type)
            return

        # Không có số → hiện danh sách
        if not val:
            lines = [f"🖼️ LỊCH SỬ AVATAR ({len(history)} ảnh)\n━━━━━━━━━━━━━━━━━━"]
            for i, e in enumerate(history, 1):
                note = f" [{e['note']}]" if e.get("note") else ""
                url_short = e['url'][:70] + ("..." if len(e['url']) > 70 else "")
                lines.append(f"{i}. {e['at']}{note}\n   {url_short}")
            lines.append(f"━━━━━━━━━━━━━━━━━━\nDùng: {cmd} avatarOld <số> để set lại")
            _reply(client, "\n\n".join(lines), message_object, thread_id, thread_type)
            return

        # Có số → set lại
        try:
            idx = int(val) - 1
        except ValueError:
            _reply(client, f"❌ Nhập số thứ tự. Ví dụ: {cmd} avatarOld 1",
                   message_object, thread_id, thread_type)
            return

        if idx < 0 or idx >= len(history):
            _reply(client, f"❌ Chọn từ 1 đến {len(history)}.",
                   message_object, thread_id, thread_type)
            return

        chosen = history[idx]
        _reply(client, f"⏳ Đang set lại avatar #{idx+1} ({chosen['at']})...",
               message_object, thread_id, thread_type)

        def _do_restore(entry, i):
            try:
                tmp = _download_image(entry["url"])
                if not tmp:
                    _reply(client, "❌ Không tải được ảnh. URL có thể đã hết hạn.",
                           message_object, thread_id, thread_type)
                    return
                p = _get_profile(client)
                old = p.get("avatar", "")
                if old:
                    _push_history(old, "trước khi restore")
                client.changeAccountAvatar(tmp)
                _push_history(entry["url"], f"restore từ #{i+1}")
                try: os.remove(tmp)
                except: pass
                _reply(client, f"✅ Đã set lại avatar #{i+1} ({entry['at']})!",
                       message_object, thread_id, thread_type)
            except Exception as e:
                _reply(client, f"❌ Lỗi: {e}", message_object, thread_id, thread_type)

        threading.Thread(target=_do_restore, args=(chosen, idx), daemon=True).start()

    else:
        _reply(client, f"❓ Không hiểu lệnh. Gõ {cmd} để xem hướng dẫn.",
               message_object, thread_id, thread_type)


def LIGHT():
    return {"myacc": handle_myacc}