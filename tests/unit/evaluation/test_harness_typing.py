"""Regression tests for evaluation harness typing-sensitive helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import duckdb

from autoresearch.evaluation.harness import EvaluationHarness


def test_open_duckdb_closes_connection(tmp_path, monkeypatch):
    """``EvaluationHarness._open_duckdb`` should close the connection on exit."""

    harness = EvaluationHarness(output_dir=tmp_path, duckdb_path=tmp_path / "truth.duckdb")
    connection = MagicMock()
    monkeypatch.setattr(duckdb, "connect", MagicMock(return_value=connection))

    with harness._open_duckdb() as conn:
        assert conn is connection

    connection.close.assert_called_once()
    duckdb.connect.assert_called_once_with(str(Path(tmp_path / "truth.duckdb")))
