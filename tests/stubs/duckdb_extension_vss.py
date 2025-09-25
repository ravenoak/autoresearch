"""Typed stub for :mod:`duckdb_extension_vss`."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


class DuckDBExtensionVSSModule(Protocol):
    __version__: str


class _DuckDBExtensionVSSModule(ModuleType):
    __version__ = "0.0"
    __spec__ = importlib.util.spec_from_loader("duckdb_extension_vss", loader=None)

    def __init__(self) -> None:
        super().__init__("duckdb_extension_vss")


if importlib.util.find_spec("duckdb_extension_vss") is None:
    duckdb_extension_vss = cast(
        DuckDBExtensionVSSModule,
        install_stub_module("duckdb_extension_vss", _DuckDBExtensionVSSModule),
    )
else:  # pragma: no cover
    import duckdb_extension_vss as _duckdb_extension_vss

    duckdb_extension_vss = cast(DuckDBExtensionVSSModule, _duckdb_extension_vss)


__all__ = ["DuckDBExtensionVSSModule", "duckdb_extension_vss"]
