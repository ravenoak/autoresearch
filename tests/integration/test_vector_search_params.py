# mypy: ignore-errors
from __future__ import annotations

import duckdb
import pytest
from pathlib import Path
from typing import Any, Mapping, Sequence

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageManager
from autoresearch.storage_typing import (
    DuckDBConnectionProtocol,
    DuckDBCursorProtocol,
)

pytestmark = [pytest.mark.slow, pytest.mark.requires_vss]


class _DummyCursor(DuckDBCursorProtocol):
    """Cursor capturing executed SQL."""

    def __init__(self, commands: list[str], last_result: list[tuple[Any, ...]]) -> None:
        self._commands = commands
        self._last_result = last_result

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [tuple(row) for row in self._last_result]

    def fetchone(self) -> tuple[Any, ...] | None:
        return tuple(self._last_result[0]) if self._last_result else None


class _DummyConn(DuckDBConnectionProtocol):
    """DuckDB connection stub that records executed SQL statements."""

    def __init__(self, commands: list[str]) -> None:
        self._commands = commands
        self._cursor = _DummyCursor(commands, [("n1", [0.1, 0.2])])

    def execute(
        self,
        query: str,
        parameters: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> DuckDBCursorProtocol:
        self._commands.append(query)
        return self._cursor

    def close(self) -> None:
        return None


def test_vector_search_uses_params(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
            vector_search_batch_size=64,
            vector_search_timeout_ms=5000,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    commands: list[str] = []
    dummy = _DummyConn(commands)
    monkeypatch.setattr(duckdb, "connect", lambda p: dummy)
    monkeypatch.setattr(
        "autoresearch.extensions.VSSExtensionLoader.verify_extension", lambda c, verbose=False: True
    )

    StorageManager.setup(str(tmp_path / "kg.duckdb"))
    results: Sequence[Mapping[str, object]] = StorageManager.vector_search([0.1, 0.2], k=1)

    assert any("vss_search_batch_size=64" in cmd for cmd in commands)
    assert any("query_timeout_ms=5000" in cmd for cmd in commands)
    assert results[0]["node_id"] == "n1"
