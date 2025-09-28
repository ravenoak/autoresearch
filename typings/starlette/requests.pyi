from typing import Any, Mapping, MutableMapping

from .types import Receive, Scope, Send


class Request:
    scope: Scope
    state: Any
    headers: Mapping[str, str]
    query_params: Mapping[str, str]
    path_params: MutableMapping[str, Any]
    client: Any
    url: Any

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None: ...

    async def body(self) -> bytes: ...


__all__ = ["Request"]
