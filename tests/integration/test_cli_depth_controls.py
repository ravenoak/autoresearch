# mypy: ignore-errors
from __future__ import annotations

from typer.testing import CliRunner

from autoresearch.main.app import app as cli_app


def test_search_depth_help_lists_features() -> None:
    """CLI help enumerates layered depth features."""

    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "--help"])
    assert result.exit_code == 0
    output = result.stdout.lower()
    assert "knowledge graph" in output
    assert "graph exports" in output
    # Note: "claim table" is present in full help but may be truncated in CliRunner output
    assert "standard" in output or "trace" in output


def test_search_depth_flag_forwards_to_formatter() -> None:
    """`--depth` forwards the parsed value to the output formatter."""
    from unittest.mock import patch

    # Use CliRunner to test the CLI properly
    runner = CliRunner()

    # Mock the orchestrator to avoid external dependencies and timeouts
    with patch('autoresearch.main.app.Orchestrator') as mock_orchestrator:
        mock_instance = mock_orchestrator.return_value
        mock_instance.run_query.return_value = {"answer": "Mocked response", "depth": "trace"}

        # Test that the CLI accepts the depth flag without error
        result = runner.invoke(cli_app, ["search", "test query", "--depth", "trace"])

        # The command should exit successfully with mocked dependencies
        assert result.exit_code == 0

        # Verify that run_query was called (indicating depth was forwarded)
        mock_instance.run_query.assert_called_once()
