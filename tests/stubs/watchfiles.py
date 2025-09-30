"""Typed stub for the :mod:`watchfiles` package."""

from __future__ import annotations

from collections.abc import Generator
from types import ModuleType
from typing import Any, Iterable, Protocol, cast

from ._registry import install_stub_module


def watch(*_args: Any, **_kwargs: Any) -> Generator[tuple[str, str], None, None]:
    if False:
        yield ("", "")


class WatchfilesModule(Protocol):
    def watch(self, *args: Any, **kwargs: Any) -> Iterable[tuple[str, str]]: ...


class _WatchfilesModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("watchfiles")

    def watch(self, *args: Any, **kwargs: Any) -> Iterable[tuple[str, str]]:
        return watch(*args, **kwargs)


watchfiles = cast(WatchfilesModule, install_stub_module("watchfiles", _WatchfilesModule))

__all__ = ["WatchfilesModule", "watch", "watchfiles"]
