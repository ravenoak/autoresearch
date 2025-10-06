"""Regression tests for evaluation harness typing-sensitive helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import duckdb
from pytest import MonkeyPatch

from autoresearch.evaluation.harness import EvaluationHarness


def test_open_duckdb_closes_connection(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """``EvaluationHarness._open_duckdb`` should close the connection on exit."""

    harness: EvaluationHarness = EvaluationHarness(
        output_dir=tmp_path, duckdb_path=tmp_path / "truth.duckdb"
    )
    connection: MagicMock = MagicMock()
    connect_mock: MagicMock = MagicMock(return_value=connection)
    monkeypatch.setattr(duckdb, "connect", connect_mock)

    with harness._open_duckdb() as conn:
        assert conn is connection

    connection.close.assert_called_once()
    connect_mock.assert_called_once_with(str(Path(tmp_path / "truth.duckdb")))
