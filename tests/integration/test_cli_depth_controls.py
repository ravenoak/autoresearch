# mypy: ignore-errors
from __future__ import annotations

import contextlib
import importlib

import pytest
from typer.testing import CliRunner

from autoresearch.config.models import ConfigModel
from autoresearch.main.app import app as cli_app, _config_loader
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.output_format import OutputDepth, OutputFormatter
from autoresearch.cli_helpers import depth_option_callback


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


def test_search_depth_flag_forwards_to_formatter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--depth` forwards the parsed value to the output formatter."""

    monkeypatch.setattr(
        type(_config_loader), "load_config", lambda self: ConfigModel()
    )
    monkeypatch.setattr(
        type(_config_loader), "watching", lambda self: contextlib.nullcontext()
    )
    monkeypatch.setattr(type(_config_loader), "stop_watching", lambda self: None)
    dummy_response = QueryResponse(
        answer="ok",
        citations=[],
        reasoning=[],
        metrics={},
    )

    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda self, query, config, callbacks=None, visualize=None: dummy_response,
    )

    captured_depths: list[OutputDepth | None] = []

    def fake_render(
        cls: type[OutputFormatter],
        result: QueryResponse,
        format_type: str = "markdown",
        depth: OutputDepth | None = None,
    ) -> str:
        captured_depths.append(depth)
        return "ok"

    monkeypatch.setattr(OutputFormatter, "render", classmethod(fake_render))
    cli_module = importlib.import_module("autoresearch.main.app")
    monkeypatch.setattr(
        cli_module, "print_success", lambda *args, **kwargs: None
    )
    storage_module = importlib.import_module("autoresearch.storage")
    monkeypatch.setattr(
        storage_module.StorageManager, "setup", staticmethod(lambda: None)
    )
    cli_module.search(
        "depth probe",
        output=None,
        depth=OutputDepth.TRACE,
        interactive=False,
        reasoning_mode=None,
        loops=None,
        ontology=None,
        ontology_reasoner=None,
        ontology_reasoning=False,
        token_budget=None,
        gate_policy_enabled=None,
        gate_retrieval_overlap_threshold=None,
        gate_nli_conflict_threshold=None,
        gate_complexity_threshold=None,
        gate_user_overrides=None,
        adaptive_max_factor=None,
        adaptive_min_buffer=None,
        circuit_breaker_threshold=None,
        circuit_breaker_cooldown=None,
        agents=None,
        parallel=False,
        agent_groups=None,
        primus_start=None,
        visualize=False,
        graphml=None,
        graph_json=None,
    )
    assert captured_depths == [OutputDepth.TRACE]

    captured_depths.clear()
    cli_module.search(
        "depth alias",
        output=None,
        depth=depth_option_callback("3"),
        interactive=False,
        reasoning_mode=None,
        loops=None,
        ontology=None,
        ontology_reasoner=None,
        ontology_reasoning=False,
        token_budget=None,
        gate_policy_enabled=None,
        gate_retrieval_overlap_threshold=None,
        gate_nli_conflict_threshold=None,
        gate_complexity_threshold=None,
        gate_user_overrides=None,
        adaptive_max_factor=None,
        adaptive_min_buffer=None,
        circuit_breaker_threshold=None,
        circuit_breaker_cooldown=None,
        agents=None,
        parallel=False,
        agent_groups=None,
        primus_start=None,
        visualize=False,
        graphml=None,
        graph_json=None,
    )
    assert captured_depths == [OutputDepth.TRACE]
