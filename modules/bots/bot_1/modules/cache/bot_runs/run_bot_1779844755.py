import os
import sys
import json
import time
import requests
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType

COOKIES = "{\"_ga_RYD7END4JE\":\"GS2.2.s1777231428$o1$g1$t1777231428$j60$l0$h0\",\"_ga_YS1V643LGV\":\"GS2.1.s1777231427$o1$g0$t1777231428$j59$l0$h0\",\"_ga\":\"GA1.2.74565902.1777231427\",\"__zi\":\"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WxdEIcd4zKYdIPvg7PJbk5VvlghJ4p.1\",\"__zi-legacy\":\"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WxdEIcd4zKYdIPvg7PJbk5VvlghJ4p.1\",\"_zlang\":\"vn\",\"app.event.zalo.me\":\"5066933575052278488\",\"_gid\":\"GA1.2.159074149.1779505290\",\"_ga_3EM8ZPYYN3\":\"GS2.2.s1779505292$o4$g0$t1779505292$j60$l0$h0\",\"zpsid\":\"PxDD.455923450.10.koLiCN5zB3UBgm0iVNqiDmGENWD4I1K5GaaP1rjyU756Jb91SASq9XjzB3S\",\"zpw_sek\":\"BtDV.455923450.a0.MNNCC_Y0fTO2LedDsO2breEYmBtQkeVXYFNs-RhBohY0j-21oVBgcwBAw86vlPZqXQgaWhwtbgYEWN_EwUgbrW\"}"
IMEI = "a378c4b8-9aa1-4efa-87e5-7ebaca57f434-a0e09f4206cef88dab92b93072e25747"
PREFIX = "?"
ADMIN = ""
ADM = ["696983558841863982"]

class SubBot(ZaloAPI):
    def __init__(self):
        super().__init__(api_key="", secret_key="", imei=IMEI, session_cookies=COOKIES)
        self.prefix = PREFIX
        self.admin = ADMIN
        self.adm = ADM
        print(f"[Bot 1779844755] Started with prefix: {self.prefix}")

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            msg_text = message.strip()
            if not msg_text.startswith(self.prefix):
                return
            cmd = msg_text[len(self.prefix):].strip().lower()
            if cmd == "ping":
                self.replyMessage(Message(text="🏓 Pong!"), message_object, thread_id, thread_type)
            elif cmd == "uid":
                self.replyMessage(Message(text=f"🆔 UID: {author_id}"), message_object, thread_id, thread_type)
            elif cmd == "help" or cmd == "menu":
                help_text = f"""🤖 BOT CON 1779844755
━━━━━━━━━━━━━━━━━━━━━━
⚡ Prefix: {self.prefix}
👑 Admin: {self.admin}
━━━━━━━━━━━━━━━━━━━━━━
📝 Lệnh:
{self.prefix}ping - Kiểm tra bot
{self.prefix}uid - Lấy UID
{self.prefix}help - Menu này
{self.prefix}say <nội dung> - Nói"""
                self.replyMessage(Message(text=help_text.strip()), message_object, thread_id, thread_type)
            elif cmd.startswith("say "):
                text = cmd[4:]
                self.sendMessage(Message(text=text), thread_id, thread_type)
            else:
                self.replyMessage(Message(text=f"❌ Lệnh không tồn tại!
Dùng {self.prefix}help"), message_object, thread_id, thread_type)
        except Exception as e:
            print(f"[Bot 1779844755] Error: {e}")

if __name__ == "__main__":
    try:
        bot = SubBot()
        bot.listen(run_forever=True, delay=0, thread=True)
    except Exception as e:
        print(f"[Bot 1779844755] Fatal error: {e}")
