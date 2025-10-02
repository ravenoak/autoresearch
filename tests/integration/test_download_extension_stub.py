"""Test DuckDB extension download fallback."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

from autoresearch.storage_typing import (
    DuckDBConnectionProtocol,
    DuckDBCursorProtocol,
)


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "download_duckdb_extensions.py"
spec = importlib.util.spec_from_file_location("download_duckdb_extensions", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load download_duckdb_extensions module")
download_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download_mod)


class _FailingCursor(DuckDBCursorProtocol):
    """Cursor that reports no results."""

    def fetchall(self) -> list[tuple[Any, ...]]:
        return []

    def fetchone(self) -> tuple[Any, ...] | None:
        return None


class _FailingConn(DuckDBConnectionProtocol):
    """DuckDB connection stub that raises during installation."""

    def __init__(self) -> None:
        self._cursor = _FailingCursor()

    def execute(
        self,
        query: str,
        parameters: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> DuckDBCursorProtocol:
        return self._cursor

    def close(self) -> None:
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:  # pragma: no cover - compatibility
        return self._cursor.fetchall()

    def install_extension(self, name: str) -> None:
        raise download_mod.duckdb.Error("network unreachable")


def test_network_failure_creates_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure a stub is created when downloads fail."""

    monkeypatch.setattr(download_mod, "load_offline_env", lambda *_: {})
    monkeypatch.setattr(download_mod.duckdb, "connect", lambda *_: _FailingConn())

    dest = Path(download_mod.download_extension("vss", str(tmp_path)))
    stub = tmp_path / "extensions" / "vss" / "vss.duckdb_extension"
    assert dest == stub
    assert stub.exists()
    assert stub.stat().st_size == 0
