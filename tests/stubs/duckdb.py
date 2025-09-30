"""Typed stub for the :mod:`duckdb` package used in tests."""

from __future__ import annotations

from types import ModuleType, TracebackType
from typing import Any, ClassVar, Protocol, cast

from ._registry import install_stub_module


class DuckDBPyConnectionProtocol(Protocol):
    """Protocol describing the minimal subset of ``DuckDBPyConnection`` we use."""

    _rows: list[Any]

    def execute(self, *args: Any, **kwargs: Any) -> DuckDBPyConnectionProtocol: ...

    def fetchall(self) -> list[Any]: ...

    def fetchone(self) -> Any | None: ...

    def close(self) -> None: ...

    def __enter__(self) -> DuckDBPyConnectionProtocol: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class Error(Exception):
    """Base DuckDB exception for the stub module."""


class DuckDBModule(Protocol):
    """Protocol for the ``duckdb`` module functions consumed by the tests."""

    Error: ClassVar[type[Error]]
    DuckDBPyConnection: ClassVar[type[DuckDBPyConnectionProtocol]]

    def connect(self, *args: Any, **kwargs: Any) -> DuckDBPyConnectionProtocol: ...


class DuckDBPyConnection(DuckDBPyConnectionProtocol):
    """In-memory stub mimicking a DuckDB connection."""

    def __init__(self) -> None:
        self._rows: list[Any] = []

    def execute(self, *args: Any, **kwargs: Any) -> DuckDBPyConnection:
        return self

    def fetchall(self) -> list[Any]:
        return list(self._rows)

    def fetchone(self) -> Any | None:
        return self._rows[0] if self._rows else None

    def close(self) -> None:
        return None

    def __enter__(self) -> DuckDBPyConnection:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        return None


class _DuckDBModule(ModuleType):
    DuckDBPyConnection: ClassVar[type[DuckDBPyConnection]] = DuckDBPyConnection
    Error: ClassVar[type[Error]] = Error

    def __init__(self) -> None:
        super().__init__("duckdb")

    def connect(self, *args: Any, **kwargs: Any) -> DuckDBPyConnection:
        return DuckDBPyConnection()


duckdb = cast(DuckDBModule, install_stub_module("duckdb", _DuckDBModule))

__all__ = ["duckdb", "DuckDBModule", "DuckDBPyConnection", "DuckDBPyConnectionProtocol"]
