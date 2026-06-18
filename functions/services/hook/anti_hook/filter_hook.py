from dto.index import *
badwordHits = {}
nsfwHits = {}
nudeDetector = NudeDetector()

def filterBadwordOnMessage(this, message, data, userId, threadId, type):
    try:
        gr = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
        adminIds = gr.get("adminIds", [])
        creatorId = gr.get("creatorId")
        if userId == creatorId or userId in adminIds: return
        if this.uid not in adminIds and this.uid != creatorId: return
        if skip(this, userId, threadId): return

        s = ReadServices(this.uid)
        words = (s.get("filterBadword", {}) or {}).get(str(threadId), []) or []
        if not words: return

        c = getattr(data, "content", None)
        if isinstance(c, str):
            try: c = json.loads(c)
            except: pass

        if isinstance(c, dict):
            text = c.get("text") or c.get("content") or ""
        elif isinstance(c, str):
            text = c
        else:
            text = getattr(data, "text", "") or ""

        if not isinstance(text, str) or not text.strip(): return
        t = re.sub(r"\s+", " ", text.lower()).strip()

        hit = None
        for w in words:
            ww = re.sub(r"\s+", " ", str(w).lower()).strip()
            if ww and ww in t:
                hit = w
                break
        if not hit: return

        try: this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)
        except: pass

        key = f"{userId}:{threadId}"
        now = int(time.time())
        hits = [ts for ts in (badwordHits.get(key, []) or []) if now - ts <= 300]
        hits.append(now)
        badwordHits[key] = hits

        if len(hits) >= 3:
            try: this.blockUsers(userId, threadId)
            except: pass
            return

        try: this.sendMWarning(f"\"{hit}\" is filtered here, dont repeat.!", userId, threadId, type)
        except: pass
    except:
        pass

def filterNsfwOnMessage(this, message, data, userId, threadId, type):
    try:
        gr = this.fetchGroupInfo(threadId).gridInfoMap.get(threadId, {})
        adminIds = gr.get("adminIds", [])
        creatorId = gr.get("creatorId")
        # if userId == creatorId or userId in adminIds: return
        # if this.uid not in adminIds and this.uid != creatorId: return
        if skip(this, userId, threadId): return

        s = ReadServices(this.uid)
        cfg = (s.get("filterNsfw", {}) or {}).get(str(threadId), {}) or {}
        if not bool(cfg.get("enabled", False)): return

        try: th = float(cfg.get("threshold", 0.8))
        except: th = 0.8
        if th > 1: th /= 100.0
        if th <= 0: th = 0.05
        if th > 1: th = 1.0

        msgType = getattr(data, "msgType", "") or ""
        if msgType not in ("chat.photo", "chat.gif"): return

        urls = []
        c = getattr(data, "content", None)
        if isinstance(c, str):
            try: c = json.loads(c)
            except: c = {}
        if isinstance(c, dict):
            u = c.get("hdUrl") or c.get("href") or c.get("url") or c.get("photoUrl") or c.get("thumbUrl") or c.get("thumbnailUrl")
            if isinstance(u, str) and u.strip(): urls.append(u.strip())

        att = getattr(data, "attach", None)
        if isinstance(att, str) and att.strip():
            try: a = json.loads(att)
            except: a = None
            if isinstance(a, dict): a = [a]
            if isinstance(a, list):
                for it in a:
                    if not isinstance(it, dict): continue
                    for k in ("hdUrl","href","url","thumb","thumbUrl","thumbnailUrl"):
                        u = it.get(k)
                        if isinstance(u, str) and u.strip(): urls.append(u.strip())

        urls = list(dict.fromkeys(urls))
        if not urls: return

        os.makedirs("assets/cache", exist_ok=True)

        hard = {
            "FEMALE_GENITALIA_EXPOSED","MALE_GENITALIA_EXPOSED","ANUS_EXPOSED",
            "PENIS_EXPOSED","VAGINA_EXPOSED","FEMALE_GENITALIA_COVERED","MALE_GENITALIA_COVERED"
        }
        soft = {
            "FEMALE_BREAST_EXPOSED","FEMALE_BREAST_COVERED","NIPPLES_EXPOSED","CLEAVAGE",
            "BUTTOCKS_EXPOSED","BUTTOCKS_COVERED","UNDERWEAR","BRA","LINGERIE","THONG",
            "TORSO_EXPOSED","LOWER_BODY_EXPOSED","UPPER_BODY_EXPOSED","SKIN_EXPOSED",
            "SEXUAL_ACTIVITY","SEXUAL_POSE","SEDUCING_POSE","LEWD_GESTURE","BED_SCENE","CAMGIRL_SETUP"
        }

        bestScore = 0.0
        bestClass = None
        flagged = False

        for i, url in enumerate(urls[:5], 1):
            tmp = f"assets/cache/nsfw_{int(time.time()*1000)}_{i}.jpg"
            try:
                r = requests.get(url, stream=True, timeout=25)
                r.raise_for_status()
                size = 0
                with open(tmp, "wb") as f:
                    for ch in r.iter_content(1024 * 256):
                        if ch:
                            f.write(ch)
                            size += len(ch)
                if size < 512: continue

                res = nudeDetector.detect(tmp)
                if not isinstance(res, list) or not res: continue

                localBest = 0.0
                localClass = None

                for o in res:
                    if not isinstance(o, dict): continue
                    cls = str(o.get("class", "")).strip()
                    try: sc = float(o.get("score", 0) or 0)
                    except: sc = 0.0
                    if not cls: continue

                    if cls in hard and sc >= 0.30:
                        flagged = True
                        localBest = sc
                        localClass = cls
                        break

                    if cls in soft and sc > localBest:
                        localBest = sc
                        localClass = cls

                if localBest > bestScore:
                    bestScore = localBest
                    bestClass = localClass

                if flagged or (localBest >= th and localClass in soft):
                    flagged = True
                    break

            except:
                pass
            finally:
                try:
                    if os.path.exists(tmp): os.remove(tmp)
                except: pass

        if not flagged: return

        try: this.deleteMessage(data.msgId, data.uidFrom, data.cliMsgId, threadId)
        except: pass

        key = f"{userId}:{threadId}"
        now = int(time.time())
        hits = [t for t in (nsfwHits.get(key, []) or []) if now - t <= 300]
        hits.append(now)
        nsfwHits[key] = hits

        try:
            this.sendMWarning(
                f"I blocked nfsw, this class={bestClass or 'unknown'}",
                userId, threadId, type
            )
        except: pass

        if len(hits) >= 3:
            try: this.blockUsers(userId, threadId)
            except: pass

    except:
        pass