"""Typed stub for :mod:`kuzu`."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Dict, Iterable, Protocol, cast

from ._registry import install_stub_module


class _Result:
    def __init__(self, rows: Iterable[Any] | None = None) -> None:
        self._rows = list(rows or [])
        self._idx = 0

    def has_next(self) -> bool:
        return self._idx < len(self._rows)

    def get_next(self) -> Any:
        row = self._rows[self._idx]
        self._idx += 1
        return row


class Database:
    def __init__(self, path: str) -> None:
        self.path = path


class Connection:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.data: Dict[str, tuple[str, float]] = {}

    def execute(self, query: str, params: Dict[str, Any] | None = None) -> _Result:
        params = params or {}
        if "MERGE (c:Claim" in query:
            self.data[params["id"]] = (
                params.get("content", ""),
                float(params.get("conf", 0.0)),
            )
            return _Result([])
        if "MATCH (c:Claim" in query:
            if params.get("id") in self.data:
                return _Result([self.data[params["id"]]])
            return _Result([])
        return _Result([])

    def close(self) -> None:  # pragma: no cover - nothing to close
        return None


class KuzuModule(Protocol):
    Database: type[Database]
    Connection: type[Connection]


class _KuzuModule(ModuleType):
    Database = Database
    Connection = Connection

    def __init__(self) -> None:
        super().__init__("kuzu")


kuzu = cast(KuzuModule, install_stub_module("kuzu", _KuzuModule))

__all__ = ["Connection", "Database", "KuzuModule", "kuzu"]
