"""Dataclasses representing aggregated evaluation telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(slots=True, frozen=True)
class PlannerMetrics:
    """Aggregate planner telemetry extracted from evaluation runs."""

    avg_depth: Optional[float] = None


@dataclass(slots=True, frozen=True)
class RoutingMetrics:
    """Aggregate routing telemetry derived from orchestrator metrics."""

    avg_delta: Optional[float] = None
    total_delta: Optional[float] = None
    avg_decisions: Optional[float] = None
    strategy: Optional[str] = None


@dataclass
class EvaluationSummary:
    """Aggregated metrics for a benchmark run.

    Captures accuracy, citation coverage, contradiction rate, latency, token
    usage, loop/gating telemetry, and planner/routing metrics so longitudinal
    analyses can surface regressions in control flow policies.
    """

    dataset: str
    run_id: str
    started_at: datetime
    completed_at: datetime
    total_examples: int
    config_signature: str
    accuracy: Optional[float] = None
    citation_coverage: Optional[float] = None
    contradiction_rate: Optional[float] = None
    avg_latency_seconds: Optional[float] = None
    avg_tokens_input: Optional[float] = None
    avg_tokens_output: Optional[float] = None
    avg_tokens_total: Optional[float] = None
    avg_cycles_completed: Optional[float] = None
    gate_debate_rate: Optional[float] = None
    gate_exit_rate: Optional[float] = None
    gated_example_ratio: Optional[float] = None
    planner: PlannerMetrics = field(default_factory=PlannerMetrics)
    routing: RoutingMetrics = field(default_factory=RoutingMetrics)
    duckdb_path: Optional[Path] = field(default=None)
    example_parquet: Optional[Path] = field(default=None)
    summary_parquet: Optional[Path] = field(default=None)
    example_csv: Optional[Path] = field(default=None)
    summary_csv: Optional[Path] = field(default=None)


__all__ = [
    "EvaluationSummary",
    "PlannerMetrics",
    "RoutingMetrics",
]
