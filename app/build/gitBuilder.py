from dto.index import *
import os
import shutil
import subprocess

CONFIG = "assets/config/"
SKIP = [
    CONFIG + "login.json",
    CONFIG + "bot-manager-database.json",
    CONFIG + "database-config.json",
]

gitpath = None

def GitPath():
    global gitpath
    if gitpath:
        return gitpath

    p = shutil.which("git")
    if p:
        gitpath = p
        return p

    if os.name == "nt":
        for x in (
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
        ):
            if os.path.exists(x):
                gitpath = x
                return x

    gitpath = "git"
    return gitpath

def RunGit(args, cwd, inp=None, text=True):
    p = subprocess.run(
        [GitPath(), *args],
        cwd=cwd,
        input=inp,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
        shell=False,
    )
    return p.returncode, p.stdout, p.stderr

def NormRelPath(p):
    s = (p or "").strip().strip('"').strip("'").replace("\\", "/")
    return s.rstrip("/")

def FindRepoRoot(startpath):
    code, out, _ = RunGit(["rev-parse", "--show-toplevel"], startpath, text=True)
    return out.strip() if code == 0 else None

def ListTrackedUnder(reporoot, relpath):
    rp = NormRelPath(relpath)
    if not rp:
        return []

    code, out, _ = RunGit(["ls-files", "-z", "--", rp], reporoot, text=False)
    if code != 0 or not out:
        return []

    items = [x for x in out.split(b"\0") if x]
    return [x.decode("utf-8", "replace") for x in items]

def IsIgnored(reporoot, relpaths):
    if not relpaths:
        return set()

    data = ("\0".join(relpaths) + "\0").encode("utf-8", "replace")
    code, out, _ = RunGit(["check-ignore", "-z", "--stdin"], reporoot, inp=data, text=False)
    if code not in (0, 1) or not out:
        return set()

    items = [x for x in out.split(b"\0") if x]
    return {x.decode("utf-8", "replace") for x in items}

def SetSkip(reporoot, relpath):
    rp = NormRelPath(relpath)
    if not rp:
        return 1, "", "empty path"
    return RunGit(["update-index", "--skip-worktree", "--", rp], reporoot, text=True)

def ApplySkipWorktreeDefault(skippaths=None):
    reporoot = FindRepoRoot(os.getcwd())
    if not reporoot:
        return 0, 0, 0

    skippaths = skippaths or SKIP

    targets = []
    for p in skippaths:
        targets.extend(ListTrackedUnder(reporoot, p))

    seen = set()
    uniq = []
    for x in targets:
        if not x or x == ".." or x.startswith("../") or x in seen:
            continue
        seen.add(x)
        uniq.append(x)

    ignoredset = IsIgnored(reporoot, uniq)

    ok = fail = ignored = 0
    for rp in uniq:
        if rp in ignoredset:
            ignored += 1
            continue
        code, _, _ = SetSkip(reporoot, rp)
        if code == 0:
            ok += 1
        else:
            fail += 1

    return ok, fail, ignored

def InitGitBuild():
    ok, fail, ignored = ApplySkipWorktreeDefault(SKIP)
    if ok > 0 and fail == 0:
        logger.base("Builded git configure OK")
    return ok, fail, ignored