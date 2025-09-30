"""Typed stub for :mod:`fastmcp`."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Mapping
from types import ModuleType, TracebackType
from typing import Protocol, TypeVar, cast

from ._registry import install_stub_module

ResultT = TypeVar("ResultT", covariant=True)


class ToolCallable(Protocol[ResultT]):
    __name__: str

    def __call__(self, **params: object) -> Awaitable[ResultT] | ResultT: ...


class FastMCP:
    def __init__(self) -> None:
        self.tools: dict[str, ToolCallable[object]] = {}

    def tool(self, func: ToolCallable[ResultT]) -> ToolCallable[ResultT]:
        self.tools[func.__name__] = cast(ToolCallable[object], func)
        return func

    async def call_tool(self, name: str, params: Mapping[str, object]) -> object:
        tool = self.tools[name]
        result = tool(**dict(params))
        if inspect.isawaitable(result):
            return await cast(Awaitable[object], result)
        return result


class Client:
    def __init__(self, target: FastMCP):
        self.target = target

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # pragma: no cover - trivial
        return None

    async def call_tool(self, name: str, params: Mapping[str, object]) -> object:
        return await self.target.call_tool(name, params)


class FastMCPModule(Protocol):
    FastMCP: type[FastMCP]
    Client: type[Client]


class _FastMCPModule(ModuleType):
    FastMCP = FastMCP
    Client = Client

    def __init__(self) -> None:
        super().__init__("fastmcp")


fastmcp = cast(FastMCPModule, install_stub_module("fastmcp", _FastMCPModule))

__all__ = ["Client", "FastMCP", "FastMCPModule", "ToolCallable", "fastmcp"]
