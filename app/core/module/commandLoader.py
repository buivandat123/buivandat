from app.library.packages import *
from functions.services.hook.core_hook.extra_multibot_core import GetOwnBot, GetOwnBotByFilePath
from functions.engine.data.data import *

def LoadCommandData(Uid):
    Path = f"assets/storage/{Uid}/Command.json"
    Data = jsonLoader(Path, {"command": []})
    Out = {}
    for C in Data.get("command", []) or []:
        if isinstance(C, dict) and C.get("name"):
            Out[str(C["name"])] = C
    return Out

def SyncCommandData(Uid, LoadedCommands):
    Path = f"assets/storage/{Uid}/Command.json"
    Data = jsonLoader(Path, {"command": []})
    Arr = Data.get("command")
    if not isinstance(Arr, list):
        Arr = []
        Data["command"] = Arr

    LoadedNames = set(LoadedCommands.keys())
    NewArr = []
    ExistedMap = {}

    for It in Arr:
        if not isinstance(It, dict):
            continue
        Name = str(It.get("name") or "")
        if not Name or Name not in LoadedNames:
            continue
        ExistedMap[Name] = It
        NewArr.append(It)

    for Name, Deps in LoadedCommands.items():
        if Name in ExistedMap:
            It = ExistedMap[Name]
            It["description"] = str(Deps.get("description", "") or "")
            if "permission" not in It:
                It["permission"] = Deps.get("permission", 0)
            if "cooldown" not in It:
                It["cooldown"] = Deps.get("cooldown", 0)
            if "status" not in It:
                It["status"] = Deps.get("status", True)
            if "alias" not in It:
                It["alias"] = list(Deps.get("alias", []) or [])
            continue

        NewArr.append({
            "name": Name,
            "permission": Deps.get("permission", 0),
            "description": str(Deps.get("description", "") or ""),
            "alias": list(Deps.get("alias", []) or []),
            "cooldown": Deps.get("cooldown", 0),
            "status": Deps.get("status", True)
        })

    Data["command"] = NewArr
    saveJson(Path, Data)

def RemoveMention(this, data):
    try:
        Content = data.get("content", "")
        if isinstance(Content, dict):
            Content = Content.get("title", Content)
        if not isinstance(Content, str):
            return ""
        Mentions = data.get("mentions") or []
        if not isinstance(Mentions, list):
            Mentions = []
        Mentions = sorted(Mentions, key=lambda x: (x or {}).get("pos", 0), reverse=True)
        for M in Mentions:
            if not isinstance(M, dict):
                continue
            Pos = int(M.get("pos", 0) or 0)
            Len = int(M.get("len", 0) or 0)
            if Len > 0 and Pos >= 0:
                Content = Content[:Pos] + Content[Pos + Len:]
        return " ".join(Content.split()).strip()
    except:
        return ""

def picker(Val, I, Default=None):
    if isinstance(Val, (list, tuple)):
        return Val[I] if 0 <= I < len(Val) else Default
    return Val if Val is not None else Default

def boolDependencies(Val, Default=False):
    if Val is None:
        return Default
    return bool(Val)

def inter(Val, Default=0):
    try:
        return int(Val)
    except:
        return Default

def floater(Val, Default=0.0):
    try:
        return float(Val)
    except:
        return Default

def aliasChecker(Alias, I, Multi=False):
    if not Alias:
        return []
    if isinstance(Alias, (list, tuple)):
        HasNested = any(isinstance(x, (list, tuple, set)) for x in Alias)
        if HasNested:
            V = picker(Alias, I, [])
            if isinstance(V, (list, tuple, set)):
                return list(V)
            return []
        if not Multi:
            return list(Alias)
        return []
    return []

def normalizeDeps(DepsRaw):
    if not isinstance(DepsRaw, dict):
        return []

    Names = DepsRaw.get("name")
    Main = DepsRaw.get("main")

    if isinstance(Names, (list, tuple)):
        Names = [str(x).strip() for x in Names if str(x).strip()]
        Multi = True
    else:
        Names = [str(Names).strip()] if str(Names or "").strip() else []
        Multi = False

    if not Names:
        return []

    IfMainList = isinstance(Main, (list, tuple))
    IfMainOne = callable(Main)

    if Multi:
        if not IfMainList:
            return []
        MainList = list(Main)
        if len(MainList) < len(Names):
            return []
    else:
        if IfMainList:
            MainList = list(Main)
            if not MainList or not callable(MainList[0]):
                return []
            Main = MainList[0]
        elif not IfMainOne:
            return []
        MainList = [Main]

    Perm = DepsRaw.get("permission", 0)
    NoPrefix = DepsRaw.get("noPrefix", False)
    IsMain = DepsRaw.get("isMain", False)
    Alias = DepsRaw.get("alias", [])
    Cooldown = DepsRaw.get("cooldown", 0)
    Status = DepsRaw.get("status", True)
    Desc = DepsRaw.get("description", "")

    Out = []
    for I, Name in enumerate(Names):
        MainFn = picker(MainList, I, None)
        if not callable(MainFn):
            continue

        It = {}
        It["name"] = Name
        It["main"] = MainFn
        It["permission"] = inter(picker(Perm, I, 0), 0)
        It["noPrefix"] = boolDependencies(picker(NoPrefix, I, False), False)
        It["isMain"] = boolDependencies(picker(IsMain, I, False), False)
        It["alias"] = aliasChecker(Alias, I, Multi=Multi)
        It["cooldown"] = floater(picker(Cooldown, I, 0), 0)
        It["status"] = boolDependencies(picker(Status, I, True), True)
        It["description"] = str(picker(Desc, I, "") or "")
        Out.append(It)

    return Out

def Loader(this, CommandDir: str):
    Commands = {}
    if CommandDir not in sys.path:
        sys.path.insert(0, CommandDir)

    for Root, _, Files in os.walk(CommandDir):
        for File in Files:
            if not File.endswith(".py") or File.startswith("__"):
                continue

            Path = os.path.join(Root, File)
            ModuleName = os.path.relpath(Path, CommandDir).replace(os.sep, ".").replace(".py", "")

            try:
                Spec = importlib.util.spec_from_file_location(ModuleName, Path)
                if not Spec or not Spec.loader:
                    continue

                Module = importlib.util.module_from_spec(Spec)
                Module.__package__ = ModuleName.rpartition(".")[0]
                sys.modules[ModuleName] = Module
                Spec.loader.exec_module(Module)

                if not hasattr(Module, "dependencies"):
                    continue

                DepsList = normalizeDeps(getattr(Module, "dependencies", None))
                if not DepsList:
                    continue

                for Deps in DepsList:
                    if Deps.get("isMain") and not this.mainBot:
                        continue
                    Name = Deps.get("name")
                    Main = Deps.get("main")
                    if not Name or not callable(Main):
                        continue
                    Commands[Name] = Deps

            except Exception as e:
                logger.errorMeta(f"Failed to load: {Path} | {e}")

    SyncCommandData(this.uid, Commands)
    return Commands

def _NormalizePrefixCommand(this, text):
    s = str(text or "")
    p = str(getattr(this, "prefix", "") or "")
    if not p:
        return s
    sp = p + " "
    if s.startswith(sp):
        return p + s[len(sp):].lstrip()
    return s

class CommandHandlesFunctions:
    cooldown = {}

    def InitCheckPrefix(this):
        now = time.time()
        ts = getattr(this, "prefixTs", 0)
        if now - ts < 2:
            return
        this.prefixTs = now
        try:
            bot = None
            fp = None
            try:
                bot, fp, _ = GetOwnBotByFilePath(this)
            except:
                bot = None

            if not bot:
                try:
                    bot, fp, _ = GetOwnBot(this, None, None, None, None)
                except:
                    bot = None
            if not bot:
                return
            p = str(bot.get("prefix") or "").strip()
            if p and p != getattr(this, "prefix", ""):
                this.prefix = p
        except:
            return

    def PermissionLevel(this, UserId, ThreadId):
        if str(UserId) == str(this.uid):
            return 4

        Settings = ReadServices(this.uid)

        if UserId in (Settings.get("highAdmin") or []):
            return 3
        if UserId in (Settings.get("adminBot") or []):
            return 2
        if UserId in (Settings.get("groupAdmin") or {}).get(ThreadId, []):
            return 1
        return 0

    def PermissionName(this, Level):
        try:
            L = int(Level or 0)
        except:
            L = 0
        if L >= 4:
            return "Highest Permission"
        if L == 3:
            return "High Admin"
        if L == 2:
            return "Admin Bot"
        if L == 1:
            return "Group Admin"
        return "User"

    def CheckPermission(this, UserId, ThreadId, Required):
        try:
            R = int(Required or 0)
        except:
            R = 0
        if R <= 0:
            return True
        if R == 4:
            return str(UserId) == str(this.uid)
        return this.PermissionLevel(UserId, ThreadId) >= R

    def CheckCooldown(this, UserId, Cmd, Seconds):
        try:
            Seconds = float(Seconds or 0)
        except:
            Seconds = 0
        if Seconds <= 0:
            return 0

        Key = (UserId, Cmd)
        Now = time.time()
        Last = this.cooldown.get(Key)

        if Last is None:
            this.cooldown[Key] = Now
            return 0

        Remain = Seconds - (Now - Last)
        if Remain > 0:
            return Remain

        this.cooldown[Key] = Now
        return 0

    def LoadCommands(this, message, data, UserId, ThreadId, Type):
        this.InitCheckPrefix()

        Text = RemoveMention(this, data)
        if not Text:
            return

        Text = _NormalizePrefixCommand(this, Text)

        Tokens = Text.split()
        if not Tokens:
            return

        HasPrefix = Text.startswith(this.prefix)
        try:
            RawCmd = (Text[len(this.prefix):].split()[0].lower() if HasPrefix else Tokens[0].lower()) if Tokens else ''
        except (IndexError, AttributeError):
            return

        Config = LoadCommandData(this.uid)
        Command = this.commands.get(RawCmd)
        RealCmd = RawCmd

        if not Command:
            for Name, Conf in Config.items():
                if RawCmd in (Conf.get("alias", []) or []):
                    Command = this.commands.get(Name)
                    RealCmd = Name
                    break

        if not Command:
            return

        this.rawCommand = RawCmd
        this.commandName = RealCmd
        this.hasPrefix = HasPrefix

        if not HasPrefix and not Command.get("noPrefix", False):
            return

        Conf = Config.get(RealCmd, {})
        if not Conf.get("status", Command.get("status", True)):
            return

        Level = Conf.get("permission", Command.get("permission", 0))
        try:
            Level = int(Level or 0)
        except:
            Level = 0

        if not this.CheckPermission(UserId, ThreadId, Level):
            try:
                this.sendMCustom("IGNORE", "r", f"You don't have enough permission..\nRequired: {this.PermissionName(Level)}", UserId, ThreadId, Type)
            except:
                pass
            return

        UserLevel = this.PermissionLevel(UserId, ThreadId)
        Cooldown = Conf.get("cooldown", Command.get("cooldown", 0))

        if UserLevel == 0:
            Remain = this.CheckCooldown(UserId, RealCmd, Cooldown)
            if Remain > 0:
                try:
                    for i in range(int(min(Remain, 1000)), 0, -1):
                        this.sendMultiReaction(data, "🕑", ThreadId, Type, 102229, numreact=i)
                        time.sleep(1)
                        this.sendMultiReaction(data, "", ThreadId, Type, -1, numreact=i)
                except Exception as cd:
                    logger.errorMeta(f"Cooldown err {cd}")
                return
        else:
            this.cooldown[(UserId, RealCmd)] = time.time()

        if RawCmd != RealCmd:
            if HasPrefix:
                Text = Text.replace(f"{this.prefix}{RawCmd}", f"{this.prefix}{RealCmd}", 1)
            else:
                Text = Text.replace(RawCmd, RealCmd, 1)

        try:
            this.sendReaction(data, "/-ok", ThreadId, Type, 100000000)
            Command["main"](this, Message(text=Text), data, UserId, ThreadId, Type)
        except Exception as e:
            logger.errorMeta(f"Error: {RealCmd}: {e}")