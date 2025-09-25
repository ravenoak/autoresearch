"""Typed stub for :mod:`fastmcp`."""

from __future__ import annotations

from collections.abc import Awaitable
from types import ModuleType
from typing import Any, Callable, Dict, Protocol, cast

from ._registry import install_stub_module


class FastMCP:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.tools: Dict[str, Callable[..., Awaitable[Any] | Any]] = {}

    def tool(self, func: Callable[..., Awaitable[Any] | Any]) -> Callable[..., Awaitable[Any] | Any]:
        self.tools[func.__name__] = func
        return func

    async def call_tool(self, name: str, params: dict[str, Any]) -> Any:
        tool = self.tools[name]
        result = tool(**params)
        if isinstance(result, Awaitable):
            return await result
        return result


class Client:
    def __init__(self, target: FastMCP):
        self.target = target

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None

    async def call_tool(self, name: str, params: dict[str, Any]) -> Any:
        if hasattr(self.target, "call_tool"):
            return await self.target.call_tool(name, params)
        return {}


class FastMCPModule(Protocol):
    FastMCP: type[FastMCP]
    Client: type[Client]


class _FastMCPModule(ModuleType):
    FastMCP = FastMCP
    Client = Client

    def __init__(self) -> None:
        super().__init__("fastmcp")


fastmcp = cast(FastMCPModule, install_stub_module("fastmcp", _FastMCPModule))

__all__ = ["Client", "FastMCP", "FastMCPModule", "fastmcp"]
