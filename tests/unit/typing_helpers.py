"""Shared typing helpers for unit tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, Unpack

from autoresearch.evaluation.harness import EvaluationSummary


class SummaryOverrides(TypedDict, total=False):
    """Supported overrides for :func:`build_summary_fixture`."""

    dataset: str
    run_id: str
    started_at: datetime
    completed_at: datetime
    total_examples: int
    config_signature: str
    accuracy: float | None
    citation_coverage: float | None
    contradiction_rate: float | None
    avg_latency_seconds: float | None
    avg_tokens_input: float | None
    avg_tokens_output: float | None
    avg_tokens_total: float | None
    avg_cycles_completed: float | None
    gate_debate_rate: float | None
    gate_exit_rate: float | None
    gated_example_ratio: float | None
    avg_planner_depth: float | None
    avg_routing_delta: float | None
    total_routing_delta: float | None
    avg_routing_decisions: float | None
    routing_strategy: str | None
    duckdb_path: Path | None
    example_parquet: Path | None
    summary_parquet: Path | None
    example_csv: Path | None
    summary_csv: Path | None


def build_summary_fixture(**overrides: Unpack[SummaryOverrides]) -> EvaluationSummary:
    """Return an :class:`EvaluationSummary` with sensible defaults for tests."""

    now = datetime.now(tz=timezone.utc)
    summary = EvaluationSummary(
        dataset="truthfulqa",
        run_id="run-123",
        started_at=now,
        completed_at=now,
        total_examples=1,
        config_signature="cfg",
        accuracy=0.5,
        citation_coverage=1.0,
        contradiction_rate=0.0,
        avg_latency_seconds=1.0,
        avg_tokens_input=100.0,
        avg_tokens_output=50.0,
        avg_tokens_total=150.0,
        avg_cycles_completed=1.0,
        gate_debate_rate=0.0,
        gate_exit_rate=0.25,
        gated_example_ratio=1.0,
        avg_planner_depth=2.0,
        avg_routing_delta=1.0,
        total_routing_delta=2.0,
        avg_routing_decisions=1.0,
        routing_strategy="balanced",
        duckdb_path=None,
        example_parquet=None,
        summary_parquet=None,
        example_csv=None,
        summary_csv=None,
    )
    return replace(summary, **overrides)
