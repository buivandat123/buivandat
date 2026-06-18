from dto.index import *

def aliasCommand(this, message, data, userId, threadId, type):
    text = (message.text or "").strip()
    p = this.prefix
    c = this.rawCommand
    rc = p + c

    configPath = f"assets/storage/{this.uid}/Command.json"
    config = jsonLoader(configPath, {"command": []})
    cmds = config.get("command") or []

    def _Norm(s):
        return (s or "").strip().lower()

    def _BuildMaps():
        cmdMap = { _Norm(x.get("name")): x for x in cmds if isinstance(x, dict) and x.get("name") }
        aliasMap = {}
        for x in cmds:
            name = _Norm(x.get("name"))
            if not name:
                continue
            for a in (x.get("alias") or []):
                aa = _Norm(str(a))
                if aa and aa not in aliasMap:
                    aliasMap[aa] = name
        return cmdMap, aliasMap

    def Save():
        saveJson(configPath, config)

    helpText = (
        f"""{rc} list: Get aliases list
{rc} with a command behind to add or remove alias"""
    )

    parts = text.split()
    if len(parts) < 2:
        this.sendMWarning(helpText, userId, threadId, type)
        return

    argsStr = text.split(None, 1)[1].strip()
    if _Norm(parts[1]) == "list":
        out = ["Alias list:"]
        hasAlias = False
        for x in cmds:
            aliases = x.get("alias") or []
            if aliases:
                hasAlias = True
                out.append(f"- {x.get('name')}: {', '.join(map(str, aliases))}")
        if not hasAlias:
            out.append("No aliases found")
        this.sendMSuccess("\n".join(out), userId, threadId, type)
        return

    segs = [s.strip() for s in argsStr.split(",") if s.strip()]
    if not segs:
        this.sendMWarning(helpText, userId, threadId, type)
        return

    cmdMap, aliasMap = _BuildMaps()

    def _AliasIsCmdName(a):
        a = _Norm(a)
        return a in { _Norm(k) for k in (this.commands or {}).keys() }

    changed = False

    def _RemoveAlias(alias):
        nonlocal changed
        a = _Norm(alias)
        owner = aliasMap.get(a)
        if not owner:
            return False, "not_found"
        ownerCmd = cmdMap.get(owner)
        if not ownerCmd:
            return False, "broken"
        old = ownerCmd.get("alias") or []
        new = [x for x in old if _Norm(str(x)) != a]
        if len(new) != len(old):
            ownerCmd["alias"] = new
            changed = True
            return True, owner
        return False, "not_found"

    def _ToggleAlias(cmdName, alias):
        nonlocal changed
        cmdName = _Norm(cmdName)
        a = _Norm(alias)

        if cmdName not in cmdMap:
            return False, f"Command not found: {cmdName}"

        if _AliasIsCmdName(a) and a != cmdName:
            return False, f"Alias is already a command name: {a}"

        owner = aliasMap.get(a)
        if owner and owner != cmdName:
            return False, f"{a} was set for {owner}"

        item = cmdMap[cmdName]
        item.setdefault("alias", [])
        aliases = item["alias"] or []

        if any(_Norm(str(x)) == a for x in aliases):
            item["alias"] = [x for x in aliases if _Norm(str(x)) != a]
            changed = True
            return True, f"Removed alias {a} from {cmdName}"

        item["alias"].append(a)
        changed = True
        return True, f"Added alias {a} for {cmdName}"

    isAdd = any(len(s.split()) >= 2 for s in segs)

    if not isAdd:
        removed = []
        notFound = []
        broken = []
        for s in segs:
            ok, info = _RemoveAlias(s)
            if ok:
                removed.append(s.strip())
            else:
                if info == "broken":
                    broken.append(s.strip())
                else:
                    notFound.append(s.strip())

        if changed:
            Save()

        out = []
        if removed:
            out.append("Removed:")
            out += [f"- {x}" for x in removed]
        if notFound:
            out.append("Not found:")
            out += [f"- {x}" for x in notFound]
        if broken:
            out.append("Broken map:")
            out += [f"- {x}" for x in broken]

        this.sendMSuccess("\n".join(out) if out else "No aliases changed", userId, threadId, type)
        return

    pairs = []
    first = segs[0].split()
    if len(first) >= 2 and all(len(s.split()) == 1 for s in segs[1:]):
        cmdName = first[0]
        pairs.append((cmdName, first[1]))
        for s in segs[1:]:
            pairs.append((cmdName, s))
    else:
        for s in segs:
            w = s.split()
            if len(w) >= 2:
                pairs.append((w[0], w[1]))

    okLines = []
    errLines = []
    for cmdName, a in pairs:
        ok, msg = _ToggleAlias(cmdName, a)
        if ok:
            okLines.append(f"- {msg}")
        else:
            errLines.append(f"- {msg}")

        cmdMap, aliasMap = _BuildMaps()

    if changed:
        Save()

    out = []
    if okLines:
        out.append("Updated:")
        out += okLines
    if errLines:
        out.append("Skipped:")
        out += errLines

    this.sendMSuccess("\n".join(out) if out else "No aliases changed", userId, threadId, type)

dependencies = {
    "name": "alias",
    "permission": 3,
    "description": "Command alias manage",
    "main": aliasCommand
}