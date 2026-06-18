from functions.services.hook.bot_hook.encode_core import *

def EncodeCommand(this, message, data, userId, threadId, type):
    def say(txt, s=False, w=False, f=False):
        if s:
            this.sendMSuccess(str(txt), userId, threadId, type)
        if w:
            this.sendMWarning(str(txt), userId, threadId, type)
        if f:
            this.sendMFailed(str(txt), userId, threadId, type)
        this.sendMMessage(str(txt), userId, threadId, type)

    text = (getattr(message, "text", "") or "").strip().split()

    if len(text) > 1 and str(text[1]).lower() == "list":
        out = "Encode Option:\n"
        for i, desc in enumerate(ENCODE_OPTIONS, 1):
            out += f"{i}. {desc}\n"
        say(out, True)
        return

    if len(text) < 3 or (not text[1].isdigit()) or (not text[2].isdigit()):
        say(f"Quote a python file to encode, ex: {this.prefix}{this.rawCommand} 23 5", w=True)
        return

    option = int(text[1])
    loop = int(text[2])

    if option < 1 or option > len(ENCODE_OPTIONS) or loop < 1:
        return

    sess = reqss()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    file_content_bytes = None
    filename = None

    ad = QuotedAttach(data)
    if ad and ad.get("href"):
        r = sess.get(ad["href"], headers=headers, timeout=20)
        r.raise_for_status()
        file_content_bytes = r.content
        filename = ad.get("title") or (ad["href"].split("/")[-1].split("?")[0] or "quoted.py")

    if not file_content_bytes:
        ad = attachObj(data)
        if ad and ad.get("href"):
            r = sess.get(ad["href"], headers=headers, timeout=20)
            r.raise_for_status()
            file_content_bytes = r.content
            filename = ad.get("title") or (ad["href"].split("/")[-1].split("?")[0] or "direct.py")

    if not file_content_bytes:
        for w in text[3:]:
            if isinstance(w, str) and w.startswith("http"):
                r = sess.get(w, headers=headers, timeout=20)
                r.raise_for_status()
                file_content_bytes = r.content
                filename = (w.split("/")[-1].split("?")[0] or "url.py")
                break

    if not file_content_bytes or not filename:
        say("Please quote a python files", w=True)
        return

    if not filename.lower().endswith(".py"):
        say(f"I only read python files", w=True)
        return

    try:
        src = file_content_bytes.decode("utf-8-sig")
    except:
        try:
            src = file_content_bytes.decode("utf-8", errors="ignore")
        except:
            say(f"I only read python files", w=True)
            return
    encoded_io, encoded_filename = encLogic(this, option, src, filename, loop)
    temp_zip_path = None
    try:
        zip_filename = f"{filename.replace('.py','')}.zip"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(encoded_filename, encoded_io.getvalue())
            temp_zip_path = tmp_zip.name
        href = this.uploadAttachment(temp_zip_path, threadId, type)

        file_url = href.get("fileUrl")
        sended = False
        try:
            this.sendFile(
                fileUrl=file_url,
                fileName=zip_filename,
                fileSize=os.path.getsize(temp_zip_path),
                extension="zip",
                thread_id=threadId,
                thread_type=type,
                ttl=86000000,
                local_path=temp_zip_path
            )
            sended = True
        except:
            pass

        if not sended:
            try:
                this.sendFile(
                    fileUrl=file_url,
                    fileName=zip_filename,
                    fileSize=os.path.getsize(temp_zip_path),
                    extension="zip",
                    threadId=threadId,
                    type=type,
                    ttl=86000000,
                    local_path=temp_zip_path
                )
                sended = True
            except:
                sended = False

    finally:
        if temp_zip_path and os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except:
                pass

dependencies = {
    "name": "encode",
    "permission": 0,
    "description": "Encode python file",
    "cooldown": 5,
    "main": EncodeCommand
}