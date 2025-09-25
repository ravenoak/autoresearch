"""Typed stub for the :mod:`tinydb` package."""

from __future__ import annotations

import importlib
import importlib.machinery
from types import ModuleType
from typing import Any, Callable, List, Optional, Protocol, cast

from ._registry import install_stub_module


class QueryCondition:
    """Callable wrapper representing a query condition."""

    def __init__(self, func: Callable[[dict[str, Any]], bool]):
        self.func = func

    def __call__(self, doc: dict[str, Any]) -> bool:
        return self.func(doc)

    def __and__(self, other: "QueryCondition") -> "QueryCondition":
        return QueryCondition(lambda doc: self(doc) and other(doc))

    def __or__(self, other: "QueryCondition") -> "QueryCondition":
        return QueryCondition(lambda doc: self(doc) or other(doc))


class Query:
    """Very small implementation of :class:`tinydb.queries.Query`."""

    def __init__(self, path: Optional[List[str]] = None) -> None:
        self._path: List[str] = path or []

    def __getattr__(self, item: str) -> "Query":
        return Query(self._path + [item])

    def _extract(self, doc: dict[str, Any]) -> Any:
        value: Any = doc
        for part in self._path:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
            if value is None:
                break
        return value

    def __eq__(self, other: Any) -> QueryCondition:  # type: ignore[override]
        return QueryCondition(lambda doc: self._extract(doc) == other)

    def __ne__(self, other: Any) -> QueryCondition:  # type: ignore[override]
        return QueryCondition(lambda doc: self._extract(doc) != other)


class TinyDB:
    """Simplistic in-memory TinyDB replacement."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._data: List[dict[str, Any]] = []

    def table(self, name: str) -> "TinyDB":
        return self

    def truncate(self) -> None:
        self._data.clear()
        return None

    def drop_tables(self) -> None:
        self._data.clear()

    def upsert(self, doc: dict[str, Any], cond: QueryCondition) -> None:
        for index, existing in enumerate(self._data):
            if cond(existing):
                self._data[index] = doc
                break
        else:
            self._data.append(doc)

    def get(self, cond: QueryCondition) -> Optional[dict[str, Any]]:
        for doc in self._data:
            if cond(doc):
                return doc
        return None

    def close(self) -> None:  # pragma: no cover - nothing to close
        return None


class TinyDBModule(Protocol):
    TinyDB: type[TinyDB]
    Query: type[Query]
    __spec__: importlib.machinery.ModuleSpec


class _TinyDBModule(ModuleType):
    TinyDB = TinyDB
    Query = Query
    __spec__ = importlib.machinery.ModuleSpec("tinydb", loader=None)

    def __init__(self) -> None:
        super().__init__("tinydb")


def _factory() -> _TinyDBModule:
    return _TinyDBModule()


try:  # pragma: no cover - exercised when real tinydb is installed
    tinydb = cast(TinyDBModule, importlib.import_module("tinydb"))
except Exception:  # pragma: no cover
    tinydb = cast(TinyDBModule, install_stub_module("tinydb", _factory))


__all__ = ["Query", "QueryCondition", "TinyDB", "TinyDBModule", "tinydb"]
