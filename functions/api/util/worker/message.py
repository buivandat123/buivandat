import json
from .. import utils
from ..core.Enum import Enum
from ..core.parse import Parse

class Message:
    def __init__(this, text=None, style=None, mention=None, parse_mode=None):
        this.text, this.mention = text, str(mention) if mention else None
        this.style = str(style) if style else None
        this.parse_mode = str(parse_mode) if parse_mode else None
        if not parse_mode:
            return

        baseStyles = json.loads(this.style)["styles"] if this.style else []
        if this.parse_mode not in ("Markdown", "HTML"):
            raise ValueError("Invalid Parse Mode, Only Support `Markdown` & `HTML`")

        this.text, this.parse_list = Parse(this.text, this.style, this.parse_mode)
        n = len(this.text or "")

        parsed = [
            MessageStyle(
                e["start"],
                e["length"],
                e["type"],
                e.get("color", "ffffff"),
                e.get("size", "18"),
                auto_format=False
            )
            for e in (this.parse_list or [])
        ]

        this._AddDefaultFont(parsed, n, "10")

        if len(parsed) == 1 and not baseStyles:
            this.style = json.dumps({"styles": [parsed[0]], "ver": 0})
        else:
            this.style = MultiMsgStyle(parsed + baseStyles)

        this.style = str(this.style) if this.style else None

    def _AddDefaultFont(this, styles, n, size):
        fonts = []
        for s in styles:
            st = s.get("st", "")
            if isinstance(st, str) and st.startswith("f_"):
                a = int(s.get("start", 0))
                b = a + int(s.get("len", 0))
                if b > a:
                    fonts.append((a, b))

        if n <= 0:
            return

        if not fonts:
            styles.append(MessageStyle(0, n, "font", "ffffff", str(size), auto_format=False))
            return

        fonts.sort()
        merged = []
        cs, ce = fonts[0]
        for s, e in fonts[1:]:
            if s <= ce:
                if e > ce:
                    ce = e
            else:
                merged.append((cs, ce))
                cs, ce = s, e
        merged.append((cs, ce))

        cur = 0
        for s, e in merged:
            if s > cur:
                styles.append(MessageStyle(cur, s - cur, "font", "ffffff", str(size), auto_format=False))
            if e > cur:
                cur = e
        if cur < n:
            styles.append(MessageStyle(cur, n - cur, "font", "ffffff", str(size), auto_format=False))

    def __repr__(this):
        return f"Message(text={this.text!r}, style={this.style!r}, mention={this.mention!r}, parse_mode={this.parse_mode!r})"

class MessageStyle:
    def __new__(this, offset=0, length=1, style="font", color="ffffff", size="18", auto_format=True):
        if not isinstance(offset, int) or not isinstance(length, int):
            raise ValueError("Invalid Length, Offset! Length and Offset must be integers")
        style_map = {
            "bold": "b",
            "italic": "i",
            "underline": "u",
            "strike": "s",
            "color": f"c_{str(color).replace('#', '')}",
            "font": f"f_{size}",
        }
        st = style_map.get(style, "f_18")
        data = {"start": offset, "len": length, "st": st}
        return json.dumps({"styles": [data], "ver": 0}) if auto_format else data

class MultiMsgStyle:
    def __init__(this, listStyle):
        this.styleFormat = json.dumps({"styles": listStyle, "ver": 0})
    def __str__(this):
        return this.styleFormat

class MessageReaction:
    def __new__(this, messageObject, auto_format=True):
        msg_id, cli_id = int(messageObject.msgId), int(messageObject.cliMsgId)
        msg_type = utils.getClientMessageType(messageObject.msgType)
        if not isinstance(msg_type, int):
            raise ValueError("Msg Type must be int")
        data = {"gMsgID": msg_id, "cMsgID": cli_id, "msgType": msg_type}
        return [data] if auto_format else data

class Mention:
    def __new__(this, uidOrList, length=1, offset=0, auto_format=True):
        dataList = this._Build(uidOrList, offset, length)
        return json.dumps(dataList) if auto_format else dataList

    @staticmethod
    def _One(uid, offset, length):
        if not isinstance(offset, int) or not isinstance(length, int):
            raise ValueError("Invalid Length, Offset! Length and Offset must be integers")
        uid = str(uid)
        return {"pos": offset, "len": length, "uid": uid, "type": 1 if uid == "-1" else 0}

    @classmethod
    def _Build(cls, uidOrList, offset, length):
        if isinstance(uidOrList, (list, tuple)):
            out = []
            for it in uidOrList:
                if isinstance(it, dict):
                    uid = it.get("uid")
                    off = it.get("offset", it.get("pos", 0))
                    ln = it.get("length", it.get("len", 1))
                    out.append(cls._One(uid, int(off), int(ln)))
                elif isinstance(it, (list, tuple)):
                    if len(it) == 0:
                        continue
                    uid = it[0]
                    off = it[1] if len(it) > 1 else 0
                    ln = it[2] if len(it) > 2 else 1
                    out.append(cls._One(uid, int(off), int(ln)))
                else:
                    out.append(cls._One(it, int(offset), int(length)))
            return out
        return [cls._One(uidOrList, int(offset), int(length))]