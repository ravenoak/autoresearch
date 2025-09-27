"""Step definitions for evaluation CLI scenarios."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.evaluation import EvaluationSummary
from autoresearch.cli_evaluation import EvaluationHarness

# Ensure shared step definitions are registered when this module is imported.
from . import common_steps  # noqa: F401


_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[mK]")


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from ``text``."""

    return _ANSI_PATTERN.sub("", text)


def _format_optional(value: float | None, precision: int = 2) -> str:
    """Format optional floats the same way the CLI renderer does."""

    if value is None:
        return "—"
    return f"{value:.{precision}f}"


def _format_percentage(value: float | None, precision: int = 1) -> str:
    """Format optional ratios as percentages."""

    if value is None:
        return "—"
    return f"{value * 100:.{precision}f}%"


def _format_tokens(summary: EvaluationSummary) -> str:
    """Format average token counts for assertion comparisons."""

    values = (
        summary.avg_tokens_input,
        summary.avg_tokens_output,
        summary.avg_tokens_total,
    )
    if all(value is None for value in values):
        return "—"
    formatted = [
        _format_optional(values[0], precision=1),
        _format_optional(values[1], precision=1),
        _format_optional(values[2], precision=1),
    ]
    return "/".join(formatted)


@given("the Autoresearch application is running")
def application_running_alias(temp_config) -> None:
    """Ensure the CLI runs with an isolated configuration."""

    return


@when(parsers.parse("I run `{command}`"))
def run_cli_command_alias(command: str, request) -> None:
    """Delegate CLI execution to the shared command runner."""

    cli_runner = request.getfixturevalue("cli_runner")
    bdd_context = request.getfixturevalue("bdd_context")
    isolate_network = request.getfixturevalue("isolate_network")
    restore_environment = request.getfixturevalue("restore_environment")
    common_steps.run_cli_command(
        cli_runner,
        bdd_context,
        command,
        isolate_network,
        restore_environment,
    )


@given(parsers.parse("the evaluation harness is stubbed for dataset \"{dataset}\""))
def stub_evaluation_harness(
    monkeypatch,
    tmp_path,
    bdd_context: Dict[str, Any],
    dataset: str,
) -> None:
    """Replace the evaluation harness runner with a telemetry-emitting stub."""

    artifact_dir = tmp_path / "evaluation_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    calls: List[Dict[str, Any]] = []
    expected: Dict[str, EvaluationSummary] = {}

    def _fake_run(
        self: EvaluationHarness,
        datasets: Sequence[str],
        *,
        config,
        limit: int | None = None,
        dry_run: bool = False,
        store_duckdb: bool = True,
        store_parquet: bool = True,
    ) -> List[EvaluationSummary]:
        dataset_tuple: Tuple[str, ...] = tuple(datasets)
        calls.append(
            {
                "datasets": dataset_tuple,
                "limit": limit,
                "dry_run": dry_run,
                "store_duckdb": store_duckdb,
                "store_parquet": store_parquet,
            }
        )

        summaries: List[EvaluationSummary] = []
        for ds in dataset_tuple:
            run_started = datetime.now(tz=timezone.utc)
            duckdb_path = artifact_dir / f"{ds}.duckdb"
            example_path = artifact_dir / f"{ds}_examples.parquet"
            summary_path = artifact_dir / f"{ds}_summary.parquet"

            resolved_duckdb: Path | None = None
            resolved_example: Path | None = None
            resolved_summary: Path | None = None

            if store_duckdb:
                duckdb_path.write_text("stub duckdb metrics")
                resolved_duckdb = duckdb_path
            if store_parquet:
                example_path.write_text("stub example parquet")
                summary_path.write_text("stub summary parquet")
                resolved_example = example_path
                resolved_summary = summary_path

            summary = EvaluationSummary(
                dataset=ds,
                run_id=f"{ds}-stubbed-run",
                started_at=run_started,
                completed_at=run_started,
                total_examples=4,
                accuracy=0.75,
                citation_coverage=0.5,
                contradiction_rate=0.25,
                avg_latency_seconds=2.34,
                avg_tokens_input=10.0,
                avg_tokens_output=5.0,
                avg_tokens_total=15.0,
                avg_cycles_completed=3.2,
                gate_debate_rate=0.6,
                gate_exit_rate=0.4,
                gated_example_ratio=0.5,
                config_signature="stub-signature",
                duckdb_path=resolved_duckdb,
                example_parquet=resolved_example,
                summary_parquet=resolved_summary,
            )
            summaries.append(summary)
            expected[ds] = summary

        bdd_context["expected_summaries"] = dict(expected)
        return summaries

    monkeypatch.setattr(EvaluationHarness, "run", _fake_run)
    bdd_context["harness_calls"] = calls
    bdd_context["artifact_dir"] = artifact_dir


@then(parsers.parse("the evaluation harness should receive a dry-run request for \"{dataset}\""))
def evaluation_harness_invoked(bdd_context: Dict[str, Any], dataset: str) -> None:
    """Assert that the stub harness recorded a dry-run invocation for ``dataset``."""

    calls = bdd_context.get("harness_calls", [])
    dataset_tuple = (dataset,)
    assert any(
        call.get("datasets") == dataset_tuple and call.get("dry_run") is True
        for call in calls
    ), f"Expected dry-run call for {dataset}, got {calls!r}"


@then(parsers.parse("the evaluation summary should include metrics for \"{dataset}\""))
def evaluation_summary_has_metrics(bdd_context: Dict[str, Any], dataset: str) -> None:
    """Verify that the CLI output lists summary metrics for ``dataset``."""

    result = bdd_context.get("result")
    assert result is not None, "CLI result was not captured"
    output = _strip_ansi(result.stdout)
    summaries = bdd_context.get("expected_summaries", {})
    summary = summaries.get(dataset)
    assert summary is not None, f"No stub summary recorded for {dataset}"

    expected_values = [
        dataset,
        _format_optional(summary.accuracy),
        _format_optional(summary.citation_coverage),
        _format_optional(summary.contradiction_rate),
        _format_optional(summary.avg_latency_seconds),
        _format_optional(summary.avg_cycles_completed, precision=1),
        _format_percentage(summary.gate_exit_rate),
    ]

    for value in expected_values:
        assert value in output, f"Expected '{value}' in CLI output:\n{output}"

    token_values = (
        summary.avg_tokens_input,
        summary.avg_tokens_output,
    )
    for token_value in token_values:
        if token_value is None:
            continue
        formatted = f"{token_value:.1f}"
        assert formatted in output, f"Expected token value '{formatted}' in CLI output:\n{output}"


@then(parsers.parse("the CLI output should list evaluation artifacts for \"{dataset}\""))
def evaluation_cli_lists_artifacts(bdd_context: Dict[str, Any], dataset: str) -> None:
    """Confirm that artifact paths appear in the CLI output."""

    result = bdd_context.get("result")
    assert result is not None, "CLI result was not captured"
    output = _strip_ansi(result.stdout)
    summaries = bdd_context.get("expected_summaries", {})
    summary = summaries.get(dataset)
    assert summary is not None, f"No stub summary recorded for {dataset}"

    assert "Artifacts:" in output, f"Artifacts header missing from output:\n{output}"

    if summary.duckdb_path:
        duckdb_str = str(summary.duckdb_path)
        assert "duckdb:" in output
        assert f"• {duckdb_str}" in output
    if summary.example_parquet:
        example_str = str(summary.example_parquet)
        assert "examples:" in output
        assert f"• {example_str}" in output
    if summary.summary_parquet:
        summary_str = str(summary.summary_parquet)
        assert "summary:" in output
        assert f"• {summary_str}" in output


@then("the CLI should report the dry-run warning")
def evaluation_cli_reports_dry_run(bdd_context: Dict[str, Any]) -> None:
    """Ensure the CLI emits a dry-run warning message."""

    result = bdd_context.get("result")
    assert result is not None, "CLI result was not captured"
    output = _strip_ansi(result.stdout)
    message = "Dry run completed without invoking the orchestrator."
    assert message in output, f"Expected dry-run warning in output:\n{output}"


@scenario(
    "../features/evaluation_cli.feature",
    "Render evaluation summary for a dry-run dataset",
)
def test_evaluate_cli_dry_run() -> None:
    """Drive the evaluation CLI in dry-run mode and validate its output."""

