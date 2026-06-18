from dto.index import *

def hidefile(Tb):
    if not Tb:
        return Tb
    Tb = re.sub(r'File ".*?", line', 'File "null", line', Tb)
    Tb = re.sub(r"File '.*?', line", "File 'null', line", Tb)
    Tb = re.sub(r'(/[^\s"\']+)+', "null", Tb)
    Tb = re.sub(r'([A-Za-z]:\\[^\s"\']+)+', "null", Tb)
    return Tb

def _ParseFence(s):
    s = (s or "").strip()
    m = re.match(r"^```([a-zA-Z0-9\+\#]+)?\s*\n([\s\S]*?)\n```$", s)
    if not m:
        return None, s
    tag = (m.group(1) or "").strip().lower()
    body = (m.group(2) or "").strip()
    return tag, body

def decLa(code):
    tag, body = _ParseFence(code)
    if tag in ("py", "python"):
        return "py", body
    if tag in ("js", "javascript", "node", "nodejs"):
        return "js", body
    if tag in ("cpp", "c++", "cc", "cxx"):
        return "cpp", body
    code = body if tag is not None else (code or "").strip()

    s = code.lstrip()
    if s.startswith("#include") or "using namespace std" in code or re.search(r"\bint\s+main\s*\(", code):
        return "cpp", code
    if "console.log" in code or "require(" in code or "module.exports" in code or re.search(r"\bfunction\b|\bconst\b|\blet\b", code):
        return "js", code
    return "py", code

def javascriptRun(code, timeout=6):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "main.js")
        with open(p, "w", encoding="utf-8") as f:
            f.write(code or "")
        cp = subprocess.run(["node", p], capture_output=True, text=True, timeout=timeout)
        return cp.returncode, (cp.stdout or "").rstrip(), (cp.stderr or "").rstrip()

def cppgpp(code, timeout=12):
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "main.cpp")
        exe = os.path.join(d, "a.exe" if os.name == "nt" else "a.out")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code or "")
        c1 = subprocess.run(["g++", src, "-O2", "-std=c++17", "-pipe", "-o", exe], capture_output=True, text=True, timeout=timeout)
        if c1.returncode != 0:
            err = (c1.stderr or c1.stdout or "").rstrip()
            return c1.returncode, "", err
        c2 = subprocess.run([exe], capture_output=True, text=True, timeout=timeout)
        return c2.returncode, (c2.stdout or "").rstrip(), (c2.stderr or "").rstrip()

def pyexec(code, ctx):
    err = None
    res = None
    try:
        tree = ast.parse(code)
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            expr = ast.Expression(tree.body[-1].value)
            tree.body = tree.body[:-1]
            exec(compile(tree, "<eval>", "exec"), {}, ctx)
            res = eval(compile(expr, "<eval>", "eval"), {}, ctx)
        else:
            exec(code, {}, ctx)
    except Exception:
        err = hidefile(traceback.format_exc(limit=5))
    return res, err