from dataclasses import dataclass
from typing import Any, Dict, Optional, Iterator, Tuple

@dataclass(slots=True)
class ClientEntry:
    client: Any
    data: Dict[str, Any]
    botKey: str

class GetClient:
    __slots__ = ("_clients", "_main")
    def __init__(this):
        this._clients: Dict[str, ClientEntry] = {}
        this._main: Optional[ClientEntry] = None

    def setMain(this, client: Any, data: Optional[Dict[str, Any]] = None, botKey: str = "main"):
        this._main = ClientEntry(client, dict(data or {}), str(botKey))

    def setClient(this, botIntId: Any, client: Any, data: Optional[Dict[str, Any]] = None):
        k = str(botIntId)
        this._clients[k] = ClientEntry(client, dict(data or {}), k)

    def getMain(this) -> Optional[ClientEntry]:
        return this._main

    def get(this, botIntId: Any, default: Optional[ClientEntry] = None) -> Optional[ClientEntry]:
        k = str(botIntId)
        if this._main and this._main.botKey == k:
            return this._main
        return this._clients.get(k, default)

    def __getitem__(this, botIntId: Any) -> ClientEntry:
        v = this.get(botIntId)
        if v is None:
            raise KeyError(str(botIntId))
        return v

    def __contains__(this, botIntId: Any) -> bool:
        return this.get(botIntId) is not None

    def __iter__(this) -> Iterator[str]:
        if this._main:
            yield this._main.botKey
        yield from this._clients.keys()

    def items(this) -> Iterator[Tuple[str, ClientEntry]]:
        if this._main:
            yield this._main.botKey, this._main
        yield from this._clients.items()

getClient = GetClient()