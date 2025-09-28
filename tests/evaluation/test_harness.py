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
    assert summary.avg_cycles_completed is None
    assert summary.gate_debate_rate is None
    assert summary.gate_exit_rate is None
    assert summary.gated_example_ratio == 0.0
    assert summary.avg_planner_depth is None
    assert summary.avg_routing_delta is None
    assert summary.avg_routing_decisions is None
    assert summary.total_routing_delta is None
    assert summary.example_csv is None
    assert summary.summary_csv is None


def test_harness_persists_results_and_artifacts(tmp_harness: EvaluationHarness) -> None:
    """The harness persists DuckDB and Parquet outputs when enabled."""

    call_counter = {"count": 0}

    def _runner(query: str, config: ConfigModel) -> QueryResponse:
        idx = call_counter["count"]
        call_counter["count"] += 1
        answer = (
            "No, humans cannot breathe water without assistance."
            if idx % 2 == 0
            else "Evidence is inconclusive"
        )
        status = "supported" if idx % 2 == 0 else "unsupported"
        gate_should_debate = idx % 2 == 0
        cycles_completed = 3 if gate_should_debate else 1
        routing_total = 5.0 + idx
        routing_decisions = idx + 1
        execution_metrics = {
            "total_duration_seconds": 1.2 + (0.3 * idx),
            "total_tokens": {"input": 10 + idx, "output": 5 + idx, "total": 15 + 2 * idx},
            "cycles_completed": cycles_completed,
            "model_routing_cost_savings": {"total": routing_total},
            "model_routing_decisions": [
                {"agent": "synthesizer", "recommendation": "alt"}
            ]
            * routing_decisions,
        }
        gate_events = [
            {
                "should_debate": gate_should_debate,
                "target_loops": cycles_completed,
                "reason": "test_policy",
                "tokens_saved_estimate": 42 + idx,
                "heuristics": {"score": 0.8},
                "thresholds": {"min_score": 0.5},
            }
        ]
        task_graph = {
            "tasks": [
                {"id": "t1", "depends_on": []},
                {"id": "t2", "depends_on": ["t1"]},
                {"id": "t3", "depends_on": ["t2"]},
            ],
            "edges": [
                {"source": "t1", "target": "t2"},
                {"source": "t2", "target": "t3"},
            ],
        }
        return QueryResponse(
            answer=answer,
            citations=[{"source": "test"}],
            reasoning=[],
            metrics={
                "execution_metrics": execution_metrics,
                "gate_events": gate_events,
            },
            claim_audits=[{"status": status}],
            task_graph=task_graph,
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
        limit=2,
        dry_run=False,
        store_duckdb=True,
        store_parquet=True,
    )

    summary = summaries[0]
    assert summary.accuracy is not None and pytest.approx(0.5) == summary.accuracy
    assert summary.citation_coverage == pytest.approx(1.0)
    assert summary.contradiction_rate == pytest.approx(0.5)
    assert summary.avg_latency_seconds == pytest.approx(1.35)
    assert summary.avg_tokens_input == pytest.approx(10.5)
    assert summary.avg_tokens_output == pytest.approx(5.5)
    assert summary.avg_tokens_total == pytest.approx(16.0)
    assert summary.avg_cycles_completed == pytest.approx(2.0)
    assert summary.gate_debate_rate == pytest.approx(0.5)
    assert summary.gate_exit_rate == pytest.approx(0.5)
    assert summary.gated_example_ratio == pytest.approx(1.0)
    assert summary.avg_planner_depth == pytest.approx(3.0)
    assert summary.avg_routing_delta == pytest.approx(5.5)
    assert summary.total_routing_delta == pytest.approx(11.0)
    assert summary.avg_routing_decisions == pytest.approx(1.5)
    assert summary.duckdb_path == tmp_harness.duckdb_path
    assert summary.example_parquet and summary.example_parquet.exists()
    assert summary.summary_parquet and summary.summary_parquet.exists()
    assert summary.example_csv and summary.example_csv.exists()
    assert summary.summary_csv and summary.summary_csv.exists()

    with duckdb.connect(str(summary.duckdb_path)) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM evaluation_results WHERE run_id = ?",
            [summary.run_id],
        ).fetchone()[0]
        example_rows = conn.execute(
            """
            SELECT cycles_completed, gate_should_debate, planner_depth,
                   routing_delta, routing_decision_count
            FROM evaluation_results
            WHERE run_id = ?
            ORDER BY example_id
            """,
            [summary.run_id],
        ).fetchall()
        summary_row = conn.execute(
            """
            SELECT gate_exit_rate, gate_debate_rate, avg_cycles_completed,
                   gated_example_ratio, avg_planner_depth, avg_routing_delta,
                   total_routing_delta, avg_routing_decisions
            FROM evaluation_run_summary
            WHERE run_id = ?
            """,
            [summary.run_id],
        ).fetchone()
    assert count == summary.total_examples
    assert example_rows
    assert {row[1] for row in example_rows} == {True, False}
    for cycles, _debate, depth, routing_delta, routing_count in example_rows:
        assert cycles in {1, 3}
        assert depth == pytest.approx(3.0)
        assert routing_delta in {5.0, 6.0}
        assert routing_count in {1, 2}
    assert summary_row is not None
    (
        gate_exit_rate,
        gate_debate_rate,
        avg_cycles_completed,
        gated_ratio,
        avg_depth,
        avg_routing,
        total_routing,
        avg_routing_decisions,
    ) = summary_row
    assert gate_exit_rate == pytest.approx(summary.gate_exit_rate)
    assert gate_debate_rate == pytest.approx(summary.gate_debate_rate)
    assert avg_cycles_completed == pytest.approx(summary.avg_cycles_completed)
    assert gated_ratio == pytest.approx(summary.gated_example_ratio)
    assert avg_depth == pytest.approx(summary.avg_planner_depth)
    assert avg_routing == pytest.approx(summary.avg_routing_delta)
    assert total_routing == pytest.approx(summary.total_routing_delta)
    assert avg_routing_decisions == pytest.approx(summary.avg_routing_decisions)
