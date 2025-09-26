"""Smoke tests for the truthfulness evaluation harness."""

from __future__ import annotations

from pathlib import Path
from typing import List

import duckdb
import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.evaluation import EvaluationHarness
from autoresearch.models import QueryResponse


@pytest.fixture
def tmp_harness(tmp_path: Path) -> EvaluationHarness:
    """Return an evaluation harness writing artifacts to ``tmp_path``."""

    duckdb_path = tmp_path / "metrics.duckdb"
    return EvaluationHarness(output_dir=tmp_path, duckdb_path=duckdb_path)


def test_dry_run_respects_limit_and_skips_runner(tmp_harness: EvaluationHarness) -> None:
    """Dry runs honour the limit flag and never call the orchestrator runner."""

    calls: List[str] = []

    def _runner(query: str, config: ConfigModel) -> QueryResponse:  # pragma: no cover - should not run
        calls.append(query)
        raise AssertionError("Runner should not be invoked during dry runs")

    harness = EvaluationHarness(
        output_dir=tmp_harness.output_dir,
        duckdb_path=tmp_harness.duckdb_path,
        runner=_runner,
    )
    config = ConfigModel()

    summaries = harness.run(
        ["truthfulqa"],
        config=config,
        limit=1,
        dry_run=True,
        store_duckdb=False,
        store_parquet=False,
    )

    assert not calls
    assert summaries
    summary = summaries[0]
    assert summary.dataset == "truthfulqa"
    assert summary.total_examples == 1
    assert summary.accuracy is None
    assert summary.duckdb_path is None
    assert summary.example_parquet is None
    assert summary.summary_parquet is None


def test_harness_persists_results_and_artifacts(tmp_harness: EvaluationHarness) -> None:
    """The harness persists DuckDB and Parquet outputs when enabled."""

    def _runner(query: str, config: ConfigModel) -> QueryResponse:
        if "breathe water" in query:
            answer = "No, humans cannot breathe water without assistance."
            status = "supported"
        else:
            answer = "Yes"
            status = "refuted"
        return QueryResponse(
            answer=answer,
            citations=[{"source": "test"}],
            reasoning=[],
            metrics={
                "execution_metrics": {
                    "total_duration_seconds": 1.2,
                    "total_tokens": {"input": 10, "output": 5, "total": 15},
                }
            },
            claim_audits=[{"status": status}],
        )

    harness = EvaluationHarness(
        output_dir=tmp_harness.output_dir,
        duckdb_path=tmp_harness.duckdb_path,
        runner=_runner,
    )
    config = ConfigModel()

    summaries = harness.run(
        ["truthfulqa"],
        config=config,
        dry_run=False,
        store_duckdb=True,
        store_parquet=True,
    )

    summary = summaries[0]
    assert summary.accuracy is not None and pytest.approx(0.5) == summary.accuracy
    assert summary.citation_coverage == pytest.approx(1.0)
    assert summary.contradiction_rate == pytest.approx(0.5)
    assert summary.avg_latency_seconds == pytest.approx(1.2)
    assert summary.avg_tokens_input == pytest.approx(10.0)
    assert summary.avg_tokens_output == pytest.approx(5.0)
    assert summary.avg_tokens_total == pytest.approx(15.0)
    assert summary.duckdb_path == tmp_harness.duckdb_path
    assert summary.example_parquet and summary.example_parquet.exists()
    assert summary.summary_parquet and summary.summary_parquet.exists()

    with duckdb.connect(str(summary.duckdb_path)) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM evaluation_results WHERE run_id = ?",
            [summary.run_id],
        ).fetchone()[0]
    assert count == summary.total_examples
