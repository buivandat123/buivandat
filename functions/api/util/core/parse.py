import re

def Parse(text, styles=None, parse_mode=None):
    parse_mode = parse_mode or "Markdown"
    if parse_mode == "Markdown":
        return ParseMarkdown(text)
    if parse_mode == "HTML":
        return ParseHtml(text)
    return StripSimpleHtml(text)

def ParseMarkdown(text):
    tokenToType = {
        "**": ("bold", None),
        "__": ("underline", None),
        "~~": ("strike", None),
        "_":  ("italic", None),
        "==": ("color", "#f7b503"),
        "++": ("color", "#15a85f"),
        "!!": ("color", "#db342e"),
    }

    sizeRe = re.compile(r"<textsize\s*=\s*(\d+)\s*>", re.I)

    def IsWord(ch):
        return ch is not None and (ch.isalnum() or ch == "_")

    def IsSpace(ch):
        return ch is not None and ch.isspace()

    def CanOpen(tok, prev, nxt):
        if nxt is None or IsSpace(nxt):
            return False
        if tok == "_":
            if IsWord(prev):
                return False
            if not IsWord(nxt):
                return False
            return True
        if IsSpace(nxt):
            return False
        return True

    def CanClose(tok, prev, nxt):
        if prev is None or IsSpace(prev):
            return False
        if tok == "_":
            if IsWord(nxt):
                return False
            if not IsWord(prev):
                return False
            return True
        return True

    def HasValidClose(tok, start):
        j = start
        lt = len(tok)
        while True:
            j = text.find(tok, j)
            if j == -1:
                return False
            p = text[j - 1] if j - 1 >= 0 else None
            nn = text[j + lt] if j + lt < n else None
            if CanClose(tok, p, nn):
                return True
            j += 1

    out = []
    elements = []
    stack = {k: [] for k in tokenToType}
    sizeStack = {}

    i = 0
    n = len(text)

    tokens = list(tokenToType.keys())
    tokens.sort(key=len, reverse=True)

    while i < n:
        m = sizeRe.match(text, i)
        if m:
            sz = m.group(1)
            start = sizeStack.pop(sz, None)
            if start is None:
                sizeStack[sz] = len(out)
            else:
                end = len(out)
                if end > start:
                    elements.append({"start": start, "end": end, "length": end - start, "type": "font", "size": sz})
            i = m.end()
            continue

        t = None
        for k in tokens:
            if text.startswith(k, i):
                t = k
                break

        if not t:
            out.append(text[i])
            i += 1
            continue

        lt = len(t)
        prev = text[i - 1] if i - 1 >= 0 else None
        nxt = text[i + lt] if i + lt < n else None

        if stack[t] and CanClose(t, prev, nxt):
            typ, color = tokenToType[t]
            start = stack[t].pop()
            end = len(out)
            if end > start:
                e = {"start": start, "end": end, "length": end - start, "type": typ}
                if color:
                    e["color"] = color
                elements.append(e)
            i += lt
            continue

        if CanOpen(t, prev, nxt) and HasValidClose(t, i + lt):
            stack[t].append(len(out))
            i += lt
            continue

        out.append(text[i])
        i += 1

    elements.sort(key=lambda x: x["start"])
    return "".join(out), elements

def ParseHtml(text):
    tagToType = {"b": "bold", "i": "italic", "u": "underline", "s": "strike"}
    colorMap = {"red": "#db342e", "yellow": "#f7b503", "green": "#15a85f"}

    tagRe = re.compile(r"</?(b|i|u|s|red|yellow|green|textsize)(?:\s*=\s*(\d+))?>", re.IGNORECASE)

    out = []
    elements = []
    stack = {k: [] for k in tagToType}
    colorStack = {k: [] for k in colorMap}
    sizeStack = {}

    plainLen = 0
    pos = 0

    for m in tagRe.finditer(text):
        chunk = text[pos:m.start()]
        out.append(chunk)
        plainLen += len(chunk)

        raw = m.group(0)
        k = m.group(1).lower()
        v = m.group(2)
        isClose = raw.startswith("</")

        if k in tagToType:
            if isClose:
                if stack[k]:
                    start = stack[k].pop()
                    end = plainLen
                    if end > start:
                        elements.append({"start": start, "end": end, "length": end - start, "type": tagToType[k]})
            else:
                stack[k].append(plainLen)

        elif k in colorMap:
            if isClose:
                if colorStack[k]:
                    start = colorStack[k].pop()
                    end = plainLen
                    if end > start:
                        elements.append({"start": start, "end": end, "length": end - start, "type": "color", "color": colorMap[k]})
            else:
                if colorStack[k]:
                    start = colorStack[k].pop()
                    end = plainLen
                    if end > start:
                        elements.append({"start": start, "end": end, "length": end - start, "type": "color", "color": colorMap[k]})
                else:
                    colorStack[k].append(plainLen)

        elif k == "textsize":
            if isClose:
                if v and v in sizeStack:
                    start = sizeStack.pop(v, None)
                    if start is not None:
                        end = plainLen
                        if end > start:
                            elements.append({"start": start, "end": end, "length": end - start, "type": "font", "size": v})
            else:
                if v:
                    start = sizeStack.pop(v, None)
                    if start is None:
                        sizeStack[v] = plainLen
                    else:
                        end = plainLen
                        if end > start:
                            elements.append({"start": start, "end": end, "length": end - start, "type": "font", "size": v})

        pos = m.end()

    tail = text[pos:]
    out.append(tail)
    plainLen += len(tail)

    elements.sort(key=lambda x: x["start"])
    return "".join(out), elements

def StripSimpleHtml(text):
    plain, _ = ParseHtml(text)
    return plain, []