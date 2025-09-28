"""Typer commands for the truthfulness evaluation harness."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import typer

from .cli_utils import (
    console,
    format_success,
    print_error,
    print_info,
    print_warning,
    render_evaluation_summary,
)
from .config.loader import ConfigLoader
from .evaluation import EvaluationHarness, available_datasets


evaluation_app = typer.Typer(
    help=(
        "Run curated TruthfulQA, FEVER, and HotpotQA subsets and persist telemetry "
        "metrics for longitudinal tracking, including Parquet and CSV exports."
    )
)


def _normalise_suite(suite: str) -> Sequence[str]:
    if suite.lower() == "all":
        return available_datasets()
    return [suite]


@evaluation_app.command("run")
def run_suite(
    suite: str = typer.Argument(
        ..., help="Dataset to execute: truthfulqa, fever, hotpotqa, or all."
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Optional per-dataset cap on processed examples.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Skip orchestrator execution and log placeholder metrics only.",
    ),
    output_dir: Path = typer.Option(
        Path("baseline/evaluation"),
        "--output-dir",
        "-o",
        help="Directory for DuckDB and Parquet artifacts.",
    ),
    duckdb_path: Path = typer.Option(
        Path("baseline/evaluation/truthfulness.duckdb"),
        "--duckdb-path",
        help="Override the DuckDB metrics database location.",
    ),
    no_duckdb: bool = typer.Option(
        False,
        "--no-duckdb",
        help="Do not retain DuckDB rows after Parquet export.",
    ),
    no_parquet: bool = typer.Option(
        False,
        "--no-parquet",
        help="Skip Parquet exports (DuckDB persistence still runs unless disabled).",
    ),
) -> None:
    """Execute the evaluation harness for ``suite`` and render a summary table."""

    datasets = _normalise_suite(suite)
    loader = ConfigLoader()
    config = loader.config

    harness = EvaluationHarness(output_dir=output_dir, duckdb_path=duckdb_path)
    try:
        summaries = harness.run(
            datasets,
            config=config,
            limit=limit,
            dry_run=dry_run,
            store_duckdb=not no_duckdb,
            store_parquet=not no_parquet,
        )
    except ValueError as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc

    if not summaries:
        print_warning("No datasets were executed; check the provided suite or limit.")
        raise typer.Exit(code=1)

    console.print(format_success("Evaluation run complete.", symbol=True))
    render_evaluation_summary(summaries)

    artifact_paths = set()
    for summary in summaries:
        if summary.duckdb_path:
            artifact_paths.add(summary.duckdb_path)
        if summary.example_parquet:
            artifact_paths.add(summary.example_parquet)
        if summary.summary_parquet:
            artifact_paths.add(summary.summary_parquet)
        if summary.example_csv:
            artifact_paths.add(summary.example_csv)
        if summary.summary_csv:
            artifact_paths.add(summary.summary_csv)

    if artifact_paths:
        print_info("Artifacts:")
        for path in sorted(artifact_paths):
            console.print(f"  • {path}")

    if dry_run:
        print_warning("Dry run completed without invoking the orchestrator.")
