from typing import Any, Mapping, MutableMapping, Protocol

from .types import Receive, Scope, Send


class RequestState(Protocol):
    permissions: set[str] | None
    www_authenticate: str
    view_rate_limit: tuple[Any, list[str]]
    role: str

    def __setattr__(self, name: str, value: Any) -> None: ...


class Request:
    scope: Scope
    state: RequestState
    headers: Mapping[str, str]
    query_params: Mapping[str, str]
    path_params: MutableMapping[str, Any]
    client: Any
    url: Any

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None: ...

    async def body(self) -> bytes: ...


__all__ = ["Request", "RequestState"]
