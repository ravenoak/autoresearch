"""Behavior steps for evaluation CLI scenarios."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pytest_bdd import given, scenario, then

from autoresearch.cli_evaluation import EvaluationHarness
from autoresearch.evaluation import EvaluationSummary

from . import common_steps  # noqa: F401  # Import shared steps

pytestmark = pytest.mark.behavior


@pytest.fixture
def stubbed_summary(tmp_path: Path) -> EvaluationSummary:
    """Provide a deterministic evaluation summary for telemetry assertions."""

    artifact_dir = tmp_path / "evaluation-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    return EvaluationSummary(
        dataset="truthfulqa",
        run_id="dry-run-test",
        started_at=now,
        completed_at=now,
        total_examples=2,
        accuracy=0.5,
        citation_coverage=1.0,
        contradiction_rate=0.0,
        avg_latency_seconds=1.2,
        avg_tokens_input=100.0,
        avg_tokens_output=25.0,
        avg_tokens_total=125.0,
        avg_cycles_completed=1.0,
        gate_debate_rate=0.0,
        gate_exit_rate=0.75,
        gated_example_ratio=1.0,
        config_signature="stub-config",
        avg_planner_depth=2.0,
        avg_routing_delta=0.25,
        total_routing_delta=0.5,
        avg_routing_decisions=1.0,
        routing_strategy="balanced",
        duckdb_path=artifact_dir / "truthfulqa.duckdb",
        example_parquet=artifact_dir / "truthfulqa_examples.parquet",
        summary_parquet=artifact_dir / "truthfulqa_summary.parquet",
        example_csv=artifact_dir / "truthfulqa_examples.csv",
        summary_csv=artifact_dir / "truthfulqa_summary.csv",
    )


@given("the evaluation harness runner is stubbed for telemetry")
def stub_evaluation_harness(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: dict,
    stubbed_summary: EvaluationSummary,
) -> None:
    """Patch the evaluation harness to return predictable telemetry."""

    def _fake_run(self: EvaluationHarness, _datasets, **_kwargs):
        return [stubbed_summary]

    monkeypatch.setattr(EvaluationHarness, "run", _fake_run)
    bdd_context["expected_summary"] = stubbed_summary


@then("the evaluation summary output should list the stubbed telemetry")
def assert_summary_output(bdd_context: dict) -> None:
    """Verify that the CLI output includes the telemetry table with metrics."""

    result = bdd_context["result"]
    summary: EvaluationSummary = bdd_context["expected_summary"]
    stdout = result.stdout

    assert "Evaluation run complete." in stdout

    assert summary.dataset in stdout
    assert summary.run_id.rsplit("-", 1)[0] in stdout
    assert "0.50" in stdout  # accuracy
    assert "1.00" in stdout  # citation coverage
    assert "0.00" in stdout  # contradiction rate
    assert "1.20" in stdout  # latency seconds
    assert "100.0/25." in stdout  # tokens formatting (table truncation)
    assert "1.0" in stdout  # avg loops formatting
    assert "75.0%" in stdout  # gate exit rate percentage
    assert "2.0" in stdout  # planner depth formatting
    assert "0.25/0.50 (avg 1.0 routes)" in stdout
    assert summary.config_signature in stdout


@then("the evaluation summary table should include the metric columns")
def assert_summary_columns(bdd_context: dict) -> None:
    """Ensure the rendered summary table exposes each metric column header."""

    stdout = bdd_context["result"].stdout
    sanitized = re.sub(r"\x1b\[[0-9;]*m", "", stdout)
    tokens = [
        "Dataset",
        "Accuracy",
        "Citation coverage",
        "Contradiction rate",
        "Planner depth",
        "Routing Δ (avg/total)",
        "Avg latency (s)",
        "Avg tokens in/out/total",
        "Avg loops",
        "% gated exits",
        "Run ID",
        "Config",
        "Artifacts",
    ]
    for token in tokens:
        assert token in sanitized


@then("the evaluation artifacts should reference the stubbed paths")
def assert_artifact_listing(bdd_context: dict) -> None:
    """Ensure artifact paths from the stubbed summary are printed."""

    result = bdd_context["result"]
    summary: EvaluationSummary = bdd_context["expected_summary"]
    stdout = result.stdout

    assert "Artifacts:" in stdout
    assert str(summary.duckdb_path) in stdout
    assert str(summary.example_parquet) in stdout
    assert str(summary.summary_parquet) in stdout
    assert str(summary.example_csv) in stdout
    assert str(summary.summary_csv) in stdout
    assert "Dry run completed without invoking the orchestrator." in stdout


@scenario(
    "../features/evaluation_cli.feature",
    "Dry-run evaluation produces telemetry summary and artifacts",
)
def test_evaluate_cli_dry_run() -> None:
    """Scenario: Dry-run evaluation produces telemetry summary and artifacts."""

    return None


@scenario(
    "../features/evaluation_uv_cli.feature",
    "Dry-run evaluation via uv run surfaces metrics and artifacts",
)
def test_evaluate_cli_dry_run_uv() -> None:
    """Scenario: Dry-run evaluation via uv run surfaces metrics and artifacts."""

    return None
