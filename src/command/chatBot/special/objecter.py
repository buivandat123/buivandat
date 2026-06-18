from dto.index import *

def jsonLoading(v):
    if not isinstance(v, str):
        return v
    s = v.strip()
    if not s or (s[0] not in "{["):
        return v
    try:
        return json.loads(s)
    except:
        return v

def toDict(v):
    if isinstance(v, dict):
        return {k: toDict(jsonLoading(x)) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [toDict(jsonLoading(x)) for x in v]
    if hasattr(v, "__dict__"):
        return toDict(v.__dict__)
    return jsonLoading(v)

def downloadUrl(url, downloadPath, retries=3, delay=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    }
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            with open(downloadPath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            return downloadPath
        except Exception as e:
            attempt += 1
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.errorMeta(e)
    return None

def GetQuoteHref(this, message, data, userId, threadId, type):
    q = getattr(data, "quote", None)
    if not q:
        return this.sendMWarning("No quote found.", userId, threadId, type)
    attach = getattr(q, "attach", None)
    if isinstance(attach, str):
        attach = json.loads(attach)
    href = attach.get("href")
    return this.sendMSuccess(f"Href I got: {href}", userId, threadId, type)

def checkLink(this, message, data, userId, threadId, type):
    if not data.quote:
        return this.sendMWarning(f"Quote a attachment to getlink..!", userId, threadId, type)
    quoteda = data.quote.attach
    dataA = json.loads(quoteda)
    href = dataA.get("href")
    if data.quote:
        return this.sendMSuccess(f"Link: {href}", userId, threadId, type)

def checkData(this, message, data, userId, threadId, type):
    q = getattr(data, "quote", None)
    if not q:
        return this.sendMention("Quote any messages :v", userId, threadId, type)

    payload = toDict(q)
    this.sendMSuccess(json.dumps(payload, ensure_ascii=False, indent=4), userId, threadId, type)

def getVoice(this, message, data, userId, threadId, type):
    quote = getattr(data, "quote", None)
    attach = getattr(quote, "attach", None)

    if not attach:
        return this.sendMWarning("Reply a attachment to getvoice..!", userId, threadId, type)

    attachData = json.loads(attach or "{}")
    attachUrl = attachData.get("hdUrl") or attachData.get("href")
    downloadPath = f"assets/cache/downloaded-{this.randomInt()}.aac"
    audioAttachment = downloadUrl(attachUrl, downloadPath, retries=3)
    uploaded = this.uploadAttachment(audioAttachment, threadId, type)["fileUrl"]
    this.sendVoice(uploaded, threadId, type)
    this.sendMSuccess("Here your voice..!", userId, threadId, type)
    os.remove(downloadPath)

dependencies = {
    "name": ["gethref", "getlink", "source", "getvoice"],
    "permission": 0,
    "description": ["Attachment href", "Attachment getlink", "Get Message Data", "Get Voice from quote"],
    "cooldown": 5,
    "main": [GetQuoteHref, checkLink, checkData, getVoice]
}