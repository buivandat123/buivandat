from app.core.module.commandLoader import Loader
from dto.index import *
from functions.services.init.clearpycaches import clearPyc

def _Norm(s):
    return (s or "").strip().lower()

def _BuildIndex(cmds):
    nameMap = {}
    aliasMap = {}
    for it in cmds:
        if not isinstance(it, dict):
            continue
        name = _Norm(it.get("name"))
        if not name:
            continue
        nameMap[name] = it
        for a in (it.get("alias") or []):
            a = _Norm(a)
            if a and a not in aliasMap:
                aliasMap[a] = name
    return nameMap, aliasMap

def _ResolveCmd(nameMap, aliasMap, key):
    k = _Norm(key)
    if not k:
        return None, None
    if k in nameMap:
        return k, nameMap[k]
    if k in aliasMap and aliasMap[k] in nameMap:
        n = aliasMap[k]
        return n, nameMap[n]
    return None, None

def _FindList(nameMap, aliasMap, key, limit=30):
    k = _Norm(key)
    if not k:
        return []
    exact, partial = [], []
    for n, it in nameMap.items():
        aliases = [_Norm(x) for x in (it.get("alias") or [])]
        hitExact = (n == k) or (k in aliases)
        hitPart = (k in n) or any(k in a for a in aliases)
        if hitExact:
            exact.append(it)
        elif hitPart:
            partial.append(it)
    out = exact + partial
    if len(out) > limit:
        out = out[:limit]
    seen, res = set(), []
    for it in out:
        n = _Norm(it.get("name"))
        if n and n not in seen:
            seen.add(n)
            res.append(it)
    return res

def _PermName(v):
    try:
        v = int(v or 0)
    except:
        v = 0
    m = {0: "User", 1: "Group Admin", 2: "Bot Moderator", 3: "Bot Admin", 4: "Owner"}
    return m.get(v, f"Level {v}")

def _Usage(it, p):
    u = it.get("usage") or it.get("syntax") or it.get("format") or it.get("example") or ""
    if not u:
        return ""
    u = str(u).strip()
    if u and p and u[0] not in ("!", "/", ".", "#") and not u.startswith(p):
        u = f"{p}{u}"
    return u

def _FmtSearch(items, p):
    out = []
    for i, it in enumerate(items, 1):
        name = _Norm(it.get("name"))
        desc = (it.get("description") or it.get("desc") or "").strip()
        aliases = [x for x in (it.get("alias") or []) if _Norm(x)]
        perm = _PermName(it.get("permission", 0))
        cd = int(it.get("cooldown", 0) or 0)
        usage = _Usage(it, p)

        out.append(f"{i}. {name}")
        if desc:
            out.append(f"    Description: {desc}")
        if usage:
            out.append(f"    Syntax: {usage}")
        out.append(f"    Alias: {', '.join(aliases) if aliases else 'None'}")
        out.append(f"    Permission: {perm}")
        out.append(f"    Cooldown: {cd}s")
        out.append("")
    return "\n".join(out).rstrip()

def cmdCommand(this, message, data, userId, threadId, type):
    text = (message.text or "").strip()
    parts = text.split()
    p, c = this.prefix, this.rawCommand

    configPath = f"assets/storage/{this.uid}/Command.json"
    config = jsonLoader(configPath, {"command": []})
    cmds = config.get("command") or []
    if not cmds:
        this.sendMFailed("Command data is empty", userId, threadId, type)
        return

    nameMap, aliasMap = _BuildIndex(cmds)
    pc = p + c
    commandHelp = textHelp(pc).commandHelp

    if len(parts) < 2:
        this.sendMWarning(commandHelp, userId, threadId, type)
        return

    action = _Norm(parts[1])

    if action == "load":
        debug = any(_Norm(x) == "--debug" for x in parts[2:])
        start = time.time()

        oldCmds = getattr(this, "commands", {}) or {}
        oldKeys = set(oldCmds.keys())
        oldCount = len(oldKeys)
        oldSample = sorted(oldKeys)[:20]

        hdr = [
            "$ command reload",
            f"cwd={os.getcwd()}",
            "src=src",
            f"before={oldCount}",
        ]

        try:
            this.commands.clear()

            t0 = time.time()
            newCmds = Loader(this, "src")
            t_load = time.time() - t0

            t1 = time.time()
            this.commands.update(newCmds)
            t_update = time.time() - t1

            t2 = time.time()
            clearPyc(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            t_clear = time.time() - t2

            dt = time.time() - start
            newKeys = set(newCmds.keys())
            total = len(newKeys)
            newSample = sorted(newKeys)[:20]

            added = sorted(newKeys - oldKeys)
            deleted = sorted(oldKeys - newKeys)

            if debug:
                log = "\n".join(hdr + [
                    "status=OK",
                    f"loaded={len(newCmds)}",
                    f"total={len(this.commands)}",
                    f"time.total={dt:.3f}s",
                    f"time.loader={t_load:.3f}s",
                    f"time.update={t_update:.3f}s",
                    f"time.clearpyc={t_clear:.3f}s",
                    f"keys.before.sample={oldSample}",
                    f"keys.after.sample={newSample}",
                    f"added.count={len(added)}",
                    f"deleted.count={len(deleted)}",
                    f"added.sample={added[:20]}",
                    f"deleted.sample={deleted[:20]}",
                ])
                try:
                    logger.info(log)
                except:
                    pass
                this.sendMSuccess(log, userId, threadId, type)
                return

            extra = []
            if added:
                extra.append(f"have {len(added)}")
            if deleted:
                extra.append(f"deleted {len(deleted)}")

            msg = f"Reloaded: {total} commands"
            if extra:
                msg += " (" + " or ".join(extra) + ")"

            this.sendMSuccess(msg, userId, threadId, type)
        except Exception as e:
            tb = traceback.format_exc()
            dt = time.time() - start

            log = "\n".join(hdr + [
                "status=FAILED",
                f"time.total={dt:.3f}s",
                f"error={repr(e)}",
                "traceback:",
                tb
            ])

            try:
                logger.errorMeta(log)
            except:
                pass

            this.sendMFailed(log, userId, threadId, type)
        return

    if action == "find":
        if len(parts) < 3:
            this.sendMWarning(f"Use {pc} find and behind a keyword to find commands", userId, threadId, type)
            return
        key = " ".join(parts[2:])
        found = _FindList(nameMap, aliasMap, key, limit=30)
        if not found:
            this.sendMFailed(f'No commands found for "{_Norm(key)}"', userId, threadId, type)
            return
        this.sendMSuccess(f'Search results for "{_Norm(key)}":\n\n' + _FmtSearch(found, p), userId, threadId, type)
        return

    if action in ("cooldown", "permission"):
        if len(parts) < 4:
            this.sendMWarning(
                f"Use the command with follow args: {pc} {action} [{'seconds' if action=='cooldown' else 'level'}] [command]",
                userId, threadId, type
            )
            return
        try:
            val = int(parts[2])
        except:
            this.sendMFailed(f"{'Cooldown' if action=='cooldown' else 'Permission'} must be a number", userId, threadId, type)
            return
        key = " ".join(parts[3:])
        name, it = _ResolveCmd(nameMap, aliasMap, key)
        if not it:
            this.sendMFailed(f'Command not found: "{_Norm(key)}"', userId, threadId, type)
            return
        val = max(0, val)
        if action == "cooldown":
            it["cooldown"] = val
            saveJson(configPath, config)
            this.sendMSuccess(f"Set cooldown {val}s for {name}", userId, threadId, type)
        else:
            it["permission"] = val
            saveJson(configPath, config)
            this.sendMSuccess(f"Set permission {val} for {name}", userId, threadId, type)
        return

    if action in ("on", "off"):
        if len(parts) < 3:
            this.sendMWarning(f"Use {pc} {action} and type a command behind to toggle", userId, threadId, type)
            return
        key = " ".join(parts[2:])
        name, it = _ResolveCmd(nameMap, aliasMap, key)
        if not it:
            this.sendMFailed(f'Command not found: "{_Norm(key)}"', userId, threadId, type)
            return
        it["status"] = (action == "on")
        saveJson(configPath, config)
        this.sendMSuccess(f"Command {name} is now {'enabled' if it['status'] else 'disabled'}", userId, threadId, type)
        return

dependencies = {
    "name": "command",
    "permission": 3,
    "cooldown": 5,
    "description": "Command settings",
    "main": cmdCommand
}
