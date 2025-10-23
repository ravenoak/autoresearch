"""Integration smoke tests for CLI and configuration behavior."""

import importlib
from typing import Any, Dict

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.models import QueryResponse
from autoresearch.output_format import OutputFormatter


@pytest.mark.integration
def test_autoresearch_help(cli_runner, tmp_path, monkeypatch) -> None:
    """The top-level CLI help should render without side effects."""
    from autoresearch.main.app import app

    monkeypatch.chdir(tmp_path)

    result = cli_runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Autoresearch CLI entry point" in result.stdout


@pytest.mark.integration
def test_autoresearch_search_help(cli_runner, tmp_path, monkeypatch) -> None:
    """The search command help output should remain available."""
    from autoresearch.main.app import app

    monkeypatch.chdir(tmp_path)

    result = cli_runner.invoke(app, ["search", "--help"])

    assert result.exit_code == 0
    assert "Run research queries" in result.stdout


@pytest.mark.integration
def test_config_loader_reads_temp_dir(tmp_path, monkeypatch) -> None:
    """Config loader should parse configuration data from an isolated directory."""
    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text(
        """
[core]
llm_backend = "lmstudio"
loops = 1
default_model = "mistral"

[search]
backends = ["serper"]
max_results_per_query = 1
        """.strip()
    )

    with ConfigLoader.temporary_instance(search_paths=[config_path]) as loader:
        monkeypatch.setattr("autoresearch.main.app._config_loader", loader, raising=False)
        config = loader.config

    assert config.llm_backend == "lmstudio"
    assert config.default_model == "mistral"
    assert config.search.backends == ["serper"]


@pytest.mark.integration
@pytest.mark.requires_llm
def test_search_command_executes_with_stubbed_orchestrator(
    cli_runner, tmp_path, monkeypatch
) -> None:
    """The search command should run end-to-end with orchestration patched."""
    main_app = importlib.import_module("autoresearch.main.app")

    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text(
        """
[core]
llm_backend = "lmstudio"
loops = 1
default_model = "mistral"

[search]
backends = ["serper"]
max_results_per_query = 1
        """.strip()
    )

    captured: Dict[str, Any] = {}

    def fake_format(
        cls, result: QueryResponse, format_type: str = "markdown", depth: Any | None = None, section_overrides: Dict[str, Any] | None = None
    ) -> None:
        captured["result"] = result
        captured["format_type"] = format_type
        captured["depth"] = depth
        captured["section_overrides"] = section_overrides

    class StubOrchestrator:
        """Minimal orchestrator implementation for integration smoke tests."""

        infer_relations = staticmethod(lambda: None)

        def run_query(
            self,
            query: str,
            config,
            callbacks: Dict[str, Any] | None = None,
            *,
            visualize: bool = False,
        ) -> QueryResponse:
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](0, object())
            return QueryResponse(
                query=query,
                answer="stubbed response",
                citations=[],
                reasoning=[],
                metrics={"loops": config.loops},
            )

        @staticmethod
        def run_parallel_query(query: str, config, groups) -> QueryResponse:
            raise AssertionError("Parallel execution is not expected in this smoke test")

    with ConfigLoader.temporary_instance(search_paths=[config_path]) as loader:
        monkeypatch.setattr(main_app, "_config_loader", loader, raising=False)
        monkeypatch.setattr(main_app, "Orchestrator", StubOrchestrator, raising=False)
        monkeypatch.setattr(main_app.StorageManager, "setup", lambda: None, raising=False)
        monkeypatch.setattr(main_app.StorageManager, "load_ontology", lambda *args, **kwargs: None, raising=False)
        monkeypatch.setattr(OutputFormatter, "format", classmethod(fake_format), raising=False)

        result = cli_runner.invoke(
            main_app.app,
            [
                "search",
                "--output",
                "json",
                "stub query",
            ],
            env={
                "PYTEST_CURRENT_TEST": "tests/integration/test_behavior.py::test_search_command_executes_with_stubbed_orchestrator",
            },
        )

    assert result.exit_code == 0
    assert captured["result"].answer == "stubbed response"
    assert captured["format_type"] == "json"
    assert captured["result"].query == "stub query"
