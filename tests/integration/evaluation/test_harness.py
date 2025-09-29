"""Integration tests for the evaluation harness persistence layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.evaluation.datasets import EvaluationExample
from autoresearch.evaluation.harness import EvaluationHarness
from autoresearch.models import QueryResponse


@pytest.mark.integration
def test_harness_clones_config_and_closes_connections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure the harness clones configs via ``update`` and closes DuckDB connections."""

    dataset = "truthfulqa"
    examples = [
        EvaluationExample(
            dataset=dataset,
            example_id="example-1",
            prompt="Is water breathable?",
            expected_answers=("no",),
        )
    ]

    monkeypatch.setattr(
        "autoresearch.evaluation.harness.available_datasets",
        lambda: [dataset],
    )
    monkeypatch.setattr(
        "autoresearch.evaluation.harness.load_examples",
        lambda _: examples,
    )

    copy_calls: list[dict[str, Any]] = []
    original_model_copy = ConfigModel.model_copy

    def _spy_model_copy(
        self: ConfigModel, *, update: dict[str, Any] | None = None, deep: bool = False
    ) -> ConfigModel:
        copy_calls.append({"update": update, "deep": deep})
        return original_model_copy(self, update=update, deep=deep)

    monkeypatch.setattr(ConfigModel, "model_copy", _spy_model_copy)

    class TrackingConnection:
        def __init__(self, inner: duckdb.DuckDBPyConnection) -> None:
            self._inner = inner
            self.closed = False

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        def close(self) -> None:  # pragma: no cover - exercised via context manager
            self.closed = True
            self._inner.close()

    connections: list[TrackingConnection] = []
    original_connect = duckdb.connect

    def _tracking_connect(*args: Any, **kwargs: Any) -> TrackingConnection:
        connection = original_connect(*args, **kwargs)
        wrapper = TrackingConnection(connection)
        connections.append(wrapper)
        return wrapper

    monkeypatch.setattr(duckdb, "connect", _tracking_connect)

    config = ConfigModel()

    def _runner(prompt: str, cfg: ConfigModel) -> QueryResponse:
        assert cfg is not config
        assert prompt
        return QueryResponse(
            answer="no",
            citations=[],
            reasoning=[],
            metrics={"execution_metrics": {"total_duration_seconds": 0.1}},
        )

    harness = EvaluationHarness(
        output_dir=tmp_path,
        duckdb_path=tmp_path / "metrics.duckdb",
        runner=_runner,
    )

    summaries = harness.run(
        [dataset],
        config=config,
        dry_run=False,
        store_duckdb=True,
        store_parquet=False,
    )

    assert summaries and summaries[0].duckdb_path is not None
    assert copy_calls, "Expected ConfigModel.model_copy to be invoked"
    assert copy_calls[0]["update"] == {}
    assert copy_calls[0]["deep"] is True
    assert connections, "Expected DuckDB connections to be opened"
    assert all(conn.closed for conn in connections)
