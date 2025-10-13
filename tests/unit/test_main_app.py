"""Tests for main application CLI functionality."""

import inspect
import pytest
from typer.testing import CliRunner
from unittest.mock import Mock, patch

from autoresearch.config import ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.cli_evaluation import evaluation_app, _normalise_suite
from autoresearch.evaluation import available_datasets
from autoresearch.distributed.executors import (
    _resolve_requests_session,
    _annotation_supports_mapping,
    _as_storage_queue,
    _resolve_storage_queue,
)
from autoresearch.models import QueryResponse


class TestMainApp:
    """Test cases for main application CLI."""

    def test_cli_app_creation(self):
        """Test that the CLI app is created successfully."""
        # The CLI app should be a Typer instance
        assert cli_app is not None
        assert hasattr(cli_app, 'add_typer')

    def test_cli_app_has_search_command(self) -> None:
        """Test that the CLI app has a search command."""
        # Check that search command is registered
        assert hasattr(cli_app, 'registered_commands')
        # The search command should be available
        runner = CliRunner()
        result = runner.invoke(cli_app, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout.lower()

    def test_cli_app_has_serve_command(self) -> None:
        """Test that the CLI app has a serve command."""
        runner = CliRunner()
        result = runner.invoke(cli_app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "serve" in result.stdout.lower()

    def test_cli_app_has_capabilities_command(self) -> None:
        """Test that the CLI app has a capabilities command."""
        runner = CliRunner()
        result = runner.invoke(cli_app, ["capabilities", "--help"])
        assert result.exit_code == 0
        assert "capabilities" in result.stdout.lower()

    def test_cli_app_has_completion_command(self) -> None:
        """Test that the CLI app has a completion command."""
        runner = CliRunner()
        result = runner.invoke(cli_app, ["completion", "--help"])
        assert result.exit_code == 0
        assert "completion" in result.stdout.lower()

    def test_cli_app_error_handling(self) -> None:
        """Test CLI app error handling."""
        runner = CliRunner()

        # Test with invalid command
        result = runner.invoke(cli_app, ["nonexistent-command"])
        assert result.exit_code != 0

        # Test with invalid arguments
        result = runner.invoke(cli_app, ["search"])
        assert result.exit_code != 0

    @patch("autoresearch.main.app.StorageManager.setup")
    @patch("autoresearch.main.app.Orchestrator")
    def test_search_accepts_depth_alias(
        self,
        mock_orchestrator: Mock,
        mock_storage: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Ensure depth aliases such as 'concise' are accepted by the CLI."""

        runner = CliRunner()
        mock_storage.return_value = None
        response = QueryResponse(
            answer="ok",
            citations=[],
            reasoning=["chain"],
            metrics={},
            state_id="alias-run",
        )
        mock_orchestrator.return_value.run_query.return_value = response
        monkeypatch.setattr(
            "autoresearch.main.app._config_loader.load_config",
            lambda: ConfigModel(),
        )

        result = runner.invoke(
            cli_app, ["search", "--depth", "concise", "alias coverage"]
        )

        assert result.exit_code == 0, result.stdout
        mock_orchestrator.return_value.run_query.assert_called_once()


class TestCliEvaluation:
    """Test cases for CLI evaluation functionality."""

    def test_evaluation_app_creation(self):
        """Test that the evaluation app is created successfully."""
        assert evaluation_app is not None
        assert hasattr(evaluation_app, 'add_typer')

    def test_evaluation_app_has_run_command(self):
        """Test that the evaluation app has a run command."""
        runner = CliRunner()
        result = runner.invoke(evaluation_app, ["run", "--help"])
        assert result.exit_code == 0
        assert "run" in result.stdout.lower()

    def test_normalise_suite_single_dataset(self):
        """Test _normalise_suite with single dataset."""
        result = _normalise_suite("truthfulqa")
        assert result == ["truthfulqa"]

    def test_normalise_suite_all_datasets(self):
        """Test _normalise_suite with 'all'."""
        with patch("autoresearch.cli_evaluation.available_datasets", return_value=["truthfulqa", "fever"]):
            result = _normalise_suite("all")
            assert result == ["truthfulqa", "fever"]

    def test_normalise_suite_case_insensitive(self):
        """Test _normalise_suite case insensitivity."""
        result = _normalise_suite("TRUTHFULQA")
        assert result == ["TRUTHFULQA"]

    def test_available_datasets_functionality(self):
        """Test available_datasets function."""
        datasets = available_datasets()
        assert isinstance(datasets, (list, tuple))
        assert len(datasets) > 0
        # Should contain known datasets
        known_datasets = ["truthfulqa", "fever", "hotpotqa"]
        for dataset in known_datasets:
            assert dataset in datasets


class TestDistributedExecutors:
    """Test cases for distributed executor utilities."""

    def test_resolve_requests_session_none(self):
        """Test _resolve_requests_session with None input."""
        result = _resolve_requests_session(None)
        assert result is None

    def test_resolve_requests_session_direct(self):
        """Test _resolve_requests_session with direct session."""
        from autoresearch.typing.http import RequestsSessionProtocol
        mock_session = Mock(spec=RequestsSessionProtocol)
        result = _resolve_requests_session(mock_session)
        assert result is mock_session

    def test_annotation_supports_mapping_basic_types(self):
        """Test _annotation_supports_mapping with basic types."""
        # Basic types that are not mappings should return False
        assert not _annotation_supports_mapping(str)
        assert not _annotation_supports_mapping(int)
        assert not _annotation_supports_mapping(list)

        # None and empty should return False
        assert not _annotation_supports_mapping(None)
        assert not _annotation_supports_mapping(inspect._empty)

    def test_annotation_supports_mapping_generic(self):
        """Test _annotation_supports_mapping with generic types."""
        from typing import List, Dict
        assert _annotation_supports_mapping(Dict[str, int])
        assert not _annotation_supports_mapping(List[str])

    def test_as_storage_queue_none(self):
        """Test _as_storage_queue with None input."""
        result = _as_storage_queue(None)
        assert result is None

    def test_resolve_storage_queue_none(self):
        """Test _resolve_storage_queue with None input."""
        result = _resolve_storage_queue(None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
