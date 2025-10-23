# mypy: ignore-errors
"""Tests for CLI evaluation commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from autoresearch.cli_evaluation import _normalise_suite, evaluation_app


@pytest.fixture()
def runner():
    """CLI runner for testing."""
    return CliRunner()


def test_normalise_suite_with_specific_dataset():
    """Test _normalise_suite with a specific dataset name."""
    with patch("autoresearch.cli_evaluation.available_datasets") as mock_available:
        result = _normalise_suite("truthfulqa")
        assert result == ["truthfulqa"]
        mock_available.assert_not_called()


def test_normalise_suite_with_all():
    """Test _normalise_suite with 'all' returns all available datasets."""
    with patch("autoresearch.cli_evaluation.available_datasets") as mock_available:
        mock_available.return_value = ["truthfulqa", "fever", "hotpotqa"]
        result = _normalise_suite("all")
        assert result == ["truthfulqa", "fever", "hotpotqa"]
        mock_available.assert_called_once()


def test_normalise_suite_with_all_lowercase():
    """Test _normalise_suite with 'ALL' (uppercase) returns all datasets."""
    with patch("autoresearch.cli_evaluation.available_datasets") as mock_available:
        mock_available.return_value = ["truthfulqa", "fever"]
        result = _normalise_suite("ALL")
        assert result == ["truthfulqa", "fever"]
        mock_available.assert_called_once()


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_basic_execution(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test basic suite execution."""
    # Setup mocks
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_summary = MagicMock()
    mock_summary.duckdb_path = Path("test.duckdb")
    mock_summary.example_parquet = Path("examples.parquet")
    mock_summary.summary_parquet = Path("summary.parquet")
    mock_summary.example_csv = Path("examples.csv")
    mock_summary.summary_csv = Path("summary.csv")
    mock_harness.run.return_value = [mock_summary]
    mock_harness_class.return_value = mock_harness

    # Run command
    result = runner.invoke(evaluation_app, ["run", "truthfulqa"])

    assert result.exit_code == 0
    assert "Evaluation run complete" in result.stdout
    assert "test.duckdb" in result.stdout
    assert "examples.parquet" in result.stdout

    # Verify harness was called correctly
    mock_harness_class.assert_called_once_with(
        output_dir=Path("baseline/evaluation"),
        duckdb_path=Path("baseline/evaluation/truthfulness.duckdb")
    )
    mock_harness.run.assert_called_once_with(
        ["truthfulqa"],
        config=mock_config,
        limit=None,
        dry_run=False,
        store_duckdb=True,
        store_parquet=True
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_with_all_datasets(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test running all datasets."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    with patch("autoresearch.cli_evaluation.available_datasets", return_value=["truthfulqa", "fever"]):
        result = runner.invoke(evaluation_app, ["run", "all"])

    assert result.exit_code == 0
    mock_harness.run.assert_called_once_with(
        ["truthfulqa", "fever"],
        config=mock_config,
        limit=None,
        dry_run=False,
        store_duckdb=True,
        store_parquet=True
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_with_limit(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution with limit parameter."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa", "--limit", "10"])

    assert result.exit_code == 0
    mock_harness.run.assert_called_once_with(
        ["truthfulqa"],
        config=mock_config,
        limit=10,
        dry_run=False,
        store_duckdb=True,
        store_parquet=True
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_dry_run(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution in dry run mode."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa", "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run completed without invoking the orchestrator" in result.stdout
    mock_harness.run.assert_called_once_with(
        ["truthfulqa"],
        config=mock_config,
        limit=None,
        dry_run=True,
        store_duckdb=True,
        store_parquet=True
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_custom_output_dir(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution with custom output directory."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa", "--output-dir", "/tmp/custom"])

    assert result.exit_code == 0
    mock_harness_class.assert_called_once_with(
        output_dir=Path("/tmp/custom"),
        duckdb_path=Path("/tmp/custom/truthfulness.duckdb")
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_custom_duckdb_path(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution with custom DuckDB path."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa", "--duckdb-path", "/tmp/custom.db"])

    assert result.exit_code == 0
    mock_harness_class.assert_called_once_with(
        output_dir=Path("baseline/evaluation"),
        duckdb_path=Path("/tmp/custom.db")
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_no_duckdb(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution without DuckDB storage."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa", "--no-duckdb"])

    assert result.exit_code == 0
    mock_harness.run.assert_called_once_with(
        ["truthfulqa"],
        config=mock_config,
        limit=None,
        dry_run=False,
        store_duckdb=False,
        store_parquet=True
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_no_parquet(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution without Parquet export."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = [MagicMock()]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa", "--no-parquet"])

    assert result.exit_code == 0
    mock_harness.run.assert_called_once_with(
        ["truthfulqa"],
        config=mock_config,
        limit=None,
        dry_run=False,
        store_duckdb=True,
        store_parquet=False
    )


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_error_handling(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution error handling."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.side_effect = ValueError("Test error")
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa"])

    assert result.exit_code == 1
    assert "Test error" in result.stdout


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_no_summaries_warning(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution when no datasets are executed."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_harness.run.return_value = []  # Empty summaries
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa"])

    assert result.exit_code == 1
    assert "No datasets were executed" in result.stdout


@patch("autoresearch.cli_evaluation.EvaluationHarness")
@patch("autoresearch.cli_evaluation.ConfigLoader")
@patch("autoresearch.cli_evaluation.render_evaluation_summary")
def test_run_suite_partial_artifacts(mock_render, mock_config_loader, mock_harness_class, runner):
    """Test suite execution with partial artifact paths."""
    mock_config = MagicMock()
    mock_config_loader.return_value.config = mock_config

    mock_harness = MagicMock()
    mock_summary = MagicMock()
    mock_summary.duckdb_path = None
    mock_summary.example_parquet = Path("examples.parquet")
    mock_summary.summary_parquet = None
    mock_summary.example_csv = None
    mock_summary.summary_csv = Path("summary.csv")
    mock_harness.run.return_value = [mock_summary]
    mock_harness_class.return_value = mock_harness

    result = runner.invoke(evaluation_app, ["run", "truthfulqa"])

    assert result.exit_code == 0
    assert "examples.parquet" in result.stdout
    assert "summary.csv" in result.stdout
    # Should not contain None paths
    assert "None" not in result.stdout
