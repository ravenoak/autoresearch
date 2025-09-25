"""Typed stub for :mod:`limits` used in tests."""

from __future__ import annotations

from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


def parse(value: str) -> str:
    return value


class LimitsUtilModule(Protocol):
    def parse(self, value: str) -> str: ...


class _LimitsUtilModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("limits.util")

    def parse(self, value: str) -> str:
        return parse(value)


class LimitsModule(Protocol):
    util: LimitsUtilModule


class _LimitsModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("limits")
        self.util = cast(
            LimitsUtilModule, install_stub_module("limits.util", _LimitsUtilModule)
        )


limits = cast(LimitsModule, install_stub_module("limits", _LimitsModule))

__all__ = ["LimitsModule", "LimitsUtilModule", "limits", "parse"]
