from __future__ import annotations

from typing import Any, Awaitable, Callable, Protocol

__all__ = ["Client", "FastMCP", "ToolCallable", "FastMCPModule"]

ToolCallable = Callable[..., Awaitable[Any] | Any]


class FastMCP:
    tools: dict[str, ToolCallable]

    def __init__(self, name: str, *, host: str = ..., port: int = ...) -> None: ...

    def tool(self, func: ToolCallable) -> ToolCallable: ...

    def call_tool(self, name: str, params: dict[str, Any]) -> Awaitable[Any]: ...

    def __getattr__(self, name: str) -> Any: ...


class Client:
    target: FastMCP | str

    def __init__(self, target: FastMCP | str) -> None: ...

    async def __aenter__(self) -> Client: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None: ...

    def call_tool(self, name: str, params: dict[str, Any]) -> Awaitable[Any]: ...


class FastMCPModule(Protocol):
    FastMCP: type[FastMCP]
    Client: type[Client]
