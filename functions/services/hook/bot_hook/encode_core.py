from dto.index import *
def _xor_bytes(data_bytes, key_bytes):
    return bytes(a ^ b for a, b in zip(data_bytes, key_bytes * (len(data_bytes) // len(key_bytes) + 1)))

ENCODE_OPTIONS = [
    "Encode Marshal", "Encode Zlib", "Encode Base16", "Encode Base32", "Encode Base64",
    "Encode Zlib + Base16", "Encode Zlib + Base32", "Encode Zlib + Base64",
    "Encode Marshal + Zlib", "Encode Marshal + Base16", "Encode Marshal + Base32",
    "Encode Marshal + Base64", "Encode Marshal + Zlib + Base16", "Encode Marshal + Zlib + Base32",
    "Encode Marshal + Zlib + Base64", "Simple Encode (5 Layers)",
    "Encode Marshal + Zlib + XOR + Base64", "Encode Marshal + Zlib + Double Base64",
    "Encode Marshal + Zlib + Hex + Reverse + Obf",
    "Encode Marshal + Base32 + Base64",
    "Encode Marshal + XOR Layer + Zlib + Base64",
    "Encode Marshal + Base85 + Base64",
    "Encode Marshal + Zlib + XOR + Base85 + Base64 (VIP)"
]

def _note_header():
    try:
        pyver = os.popen("python3 --version").read().strip()
        if not pyver:
            pyver = os.popen("python --version").read().strip()
    except:
        pyver = "python"
    return (
        "# Encoded\n"
        f"# Time : {time.ctime()}\n"
        f"# Python Version to run: {pyver}\n"
        "# ---------------------------------------------\n"
    )

def _validate_python_code(data):
    try:
        compile(data, "<string>", "exec")
        return True, None
    except (SyntaxError, TypeError, ValueError) as e:
        return False, str(e)

def _special_encode(data, loop):
    current_data_bytes = marshal.dumps(compile(data, "<x>", "exec"))
    for _ in range(3):
        current_data_bytes = base64.b64encode(current_data_bytes)
    current_data_bytes = zlib.compress(current_data_bytes)
    current_data_bytes = current_data_bytes[::-1]
    embedded_b64_string = base64.b64encode(current_data_bytes).decode("ascii")
    decode_chain = f"_pyzbug['__import__']('base64').b64decode('{embedded_b64_string}')[::-1]"
    decode_chain = f"_pyzbug['__import__']('zlib').decompress({decode_chain})"
    for _ in range(3):
        decode_chain = f"_pyzbug['__import__']('base64').b64decode({decode_chain})"
    exec_line = f"_pyzbug['exec'](_pyzbug['__import__']('marshal').loads({decode_chain}))"
    return exec_line, embedded_b64_string

def _vip_encode(data, loop):
    xor_key = b"\x55"
    current_data_bytes = marshal.dumps(compile(data, "<x>", "exec"))
    def vip_single_encode_step(data_bytes_input):
        compressed_bytes = zlib.compress(data_bytes_input)
        xored_bytes = _xor_bytes(compressed_bytes, xor_key)
        b85_encoded_bytes = base64.b85encode(xored_bytes)
        return base64.b64encode(b85_encoded_bytes)
    for _ in range(loop):
        current_data_bytes = vip_single_encode_step(current_data_bytes)
    current_data_bytes = current_data_bytes[::-1]
    embedded_b64_string = base64.b64encode(current_data_bytes).decode("ascii")
    nested_decode_template = (
        f"_pyzbug['__import__']('zlib').decompress("
        f"bytes([c ^ {xor_key[0]} for c in _pyzbug['__import__']('base64').b85decode("
        f"_pyzbug['__import__']('base64').b64decode({{data_placeholder}})"
        f")])"
        f")"
    )
    exec_chain = f"_pyzbug['__import__']('base64').b64decode('{embedded_b64_string}')[::-1]"
    for _ in range(loop):
        exec_chain = nested_decode_template.format(data_placeholder=exec_chain)
    exec_line = f"_pyzbug['exec'](_pyzbug['__import__']('marshal').loads({exec_chain}))"
    return exec_line, embedded_b64_string

def encLogic(this, option, data, filename, loop):
    b16 = base64.b16encode
    b32 = base64.b32encode
    b64 = base64.b64encode
    b85 = base64.b85encode

    core = {
        1:  (lambda x: x, "_pyzbug['__import__']('marshal').loads({data_var})", True),
        2:  (zlib.compress, "_pyzbug['__import__']('zlib').decompress({data_var})", False),
        3:  (base64.b16encode, "_pyzbug['__import__']('base64').b16decode({data_var})", False),
        4:  (base64.b32encode, "_pyzbug['__import__']('base64').b32decode({data_var})", False),
        5:  (base64.b64encode, "_pyzbug['__import__']('base64').b64decode({data_var})", False),
        6:  (lambda x: b16(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b16decode({data_var}))", False),
        7:  (lambda x: b32(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b32decode({data_var}))", False),
        8:  (lambda x: b64(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b64decode({data_var}))", False),
        9:  (zlib.compress, "_pyzbug['__import__']('zlib').decompress({data_var})", True),
        10: (base64.b16encode, "_pyzbug['__import__']('base64').b16decode({data_var})", True),
        11: (base64.b32encode, "_pyzbug['__import__']('base64').b32decode({data_var})", True),
        12: (base64.b64encode, "_pyzbug['__import__']('base64').b64decode({data_var})", True),
        13: (lambda x: b16(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b16decode({data_var}))", True),
        14: (lambda x: b32(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b32decode({data_var}))", True),
        15: (lambda x: b64(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b64decode({data_var}))", True),
        16: (None, "simple_encode", False),
        17: (lambda x: b64(_xor_bytes(zlib.compress(x), b"\x55")), "_pyzbug['__import__']('zlib').decompress(bytes([c ^ 0x55 for c in _pyzbug['__import__']('base64').b64decode({data_var})]))", True),
        18: (lambda x: b64(b64(zlib.compress(x))), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b64decode(_pyzbug['__import__']('base64').b64decode({data_var})))", True),
        19: (lambda x: b16(zlib.compress(x)), "_pyzbug['__import__']('zlib').decompress(_pyzbug['__import__']('base64').b16decode({data_var}))", True),
        20: (lambda x: b64(b32(x)), "_pyzbug['__import__']('base64').b32decode(_pyzbug['__import__']('base64').b64decode({data_var}))", True),
        21: (lambda x: b64(zlib.compress(_xor_bytes(x, b"\x42"))), "_pyzbug['__import__']('zlib').decompress(bytes([c ^ 0x42 for c in _pyzbug['__import__']('base64').b64decode({data_var})]))", True),
        22: (lambda x: b64(b85(x)), "_pyzbug['__import__']('base64').b85decode(_pyzbug['__import__']('base64').b64decode({data_var}))", True),
        23: (None, "vip_encode", True),
    }

    if option not in core:
        raise Exception("Invalid Option!")

    ok, err = _validate_python_code(data)
    if not ok:
        raise Exception(f"Invalid Python code: {err}")

    encode_callable, decode_template, needs_marshal_loads = core[option]

    if encode_callable is None:
        if decode_template == "simple_encode":
            exec_line, _ = _special_encode(data, loop)
        elif decode_template == "vip_encode":
            exec_line, _ = _vip_encode(data, loop)
        else:
            raise Exception("Unsupported special encoding type.")
    else:
        if needs_marshal_loads:
            current_data_bytes = marshal.dumps(compile(data, "<x>", "exec"))
        else:
            current_data_bytes = data.encode("utf-8")

        for _ in range(loop):
            current_data_bytes = encode_callable(current_data_bytes)

        current_data_bytes = current_data_bytes[::-1]
        embedded_b64_string = base64.b64encode(current_data_bytes).decode("ascii")

        exec_chain = f"_pyzbug['__import__']('base64').b64decode('{embedded_b64_string}')[::-1]"
        for _ in range(loop):
            exec_chain = decode_template.format(data_var=exec_chain)

        if needs_marshal_loads:
            exec_line = f"_pyzbug['exec'](_pyzbug['__import__']('marshal').loads({exec_chain}))"
        else:
            exec_line = f"_pyzbug['exec']({exec_chain}.decode('utf-8'))"

    obf_code = "_pyzbug = vars(globals()['__builtins__'])\n"
    obf_code += "if __name__ == '__main__' and '__file__' in globals():\n"
    obf_code += "    " + exec_line + "\n"
    obf_code += "else:\n    exit()\n"

    outname = filename.replace(".py", "") + f"{this.userName(this.uid).replace(' ', '-')}.py"
    encoded_bytes_io = io.BytesIO()
    encoded_bytes_io.write((_note_header() + obf_code).encode("utf-8"))
    encoded_bytes_io.seek(0)
    return encoded_bytes_io, outname

def reqss():
    s = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def _extract_attach_any(x):
    if not x:
        return None
    if isinstance(x, (dict, list, tuple)):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except:
            return x
    if hasattr(x, "__dict__"):
        try:
            return x.__dict__
        except:
            return None
    return None

def _find_href(obj):
    if obj is None:
        return None
    if isinstance(obj, dict):
        v = obj.get("href")
        if isinstance(v, str) and v.startswith("http"):
            return v
        for k in ("fileUrl", "url", "downloadUrl", "rawUrl", "src"):
            v = obj.get(k)
            if isinstance(v, str) and v.startswith("http"):
                return v
        for v in obj.values():
            got = _find_href(v)
            if got:
                return got
        return None
    if isinstance(obj, (list, tuple)):
        for it in obj:
            got = _find_href(it)
            if got:
                return got
        return None
    if isinstance(obj, str):
        if obj.startswith("http"):
            return obj
        try:
            j = json.loads(obj)
            return _find_href(j)
        except:
            return None
    return None

def _find_title(obj):
    if obj is None:
        return None
    if isinstance(obj, dict):
        for k in ("title", "filename", "fileName", "name"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        for v in obj.values():
            got = _find_title(v)
            if got:
                return got
        return None
    if isinstance(obj, (list, tuple)):
        for it in obj:
            got = _find_title(it)
            if got:
                return got
        return None
    if isinstance(obj, str):
        try:
            j = json.loads(obj)
            return _find_title(j)
        except:
            return None
    return None

def QuotedAttach(msgobj):
    q = getattr(msgobj, "quote", None)
    if not q:
        return None
    a = getattr(q, "attach", None)
    d = _extract_attach_any(a)
    href = _find_href(d)
    if not href and hasattr(q, "__dict__"):
        href = _find_href(q.__dict__)
    if not href and getattr(q, "msg", None):
        href = _find_href(getattr(q, "msg", None))
    if not href:
        return None
    title = _find_title(d)
    if not title and hasattr(q, "__dict__"):
        title = _find_title(q.__dict__)
    return {"href": href, "title": title}

def attachObj(msgobj):
    a = getattr(msgobj, "attach", None)
    d = _extract_attach_any(a)
    href = _find_href(d)
    if not href and hasattr(msgobj, "__dict__"):
        href = _find_href(msgobj.__dict__)
    if not href:
        return None
    title = _find_title(d)
    if not title and hasattr(msgobj, "__dict__"):
        title = _find_title(msgobj.__dict__)
    return {"href": href, "title": title}