"""Integration tests covering regression-prone imports."""

from __future__ import annotations

import importlib

import pytest
from typer import Typer

from autoresearch.agents.registry import AgentRegistry
from autoresearch.orchestration.metrics import OrchestrationMetrics


@pytest.mark.integration
def test_agents_orchestration_reexports_metrics() -> None:
    """Ensure orchestration re-exports remain wired for agent imports."""
    orchestration = importlib.import_module("autoresearch.agents.orchestration")

    metrics = orchestration.get_orchestration_metrics()

    assert isinstance(metrics, OrchestrationMetrics)
    assert "query" in orchestration.QueryState.model_fields
    assert orchestration.DialoguePhase.__module__ == "autoresearch.orchestration.phases"
    assert orchestration.ReasoningMode.__module__ == "autoresearch.orchestration.reasoning"


@pytest.mark.integration
def test_agents_registry_contains_synthesizer() -> None:
    """Verify that the synthesizer agent remains registered and importable."""
    agents = importlib.import_module("autoresearch.agents")

    assert AgentRegistry.get_class("Synthesizer") is agents.SynthesizerAgent
    assert "Synthesizer" in AgentRegistry.list_available()


@pytest.mark.integration
def test_agent_role_enum_preserves_expected_members() -> None:
    """Guard against accidental churn in agent role enumeration."""
    agents = importlib.import_module("autoresearch.agents")

    assert agents.AgentRole.SYNTHESIZER.value == "Synthesizer"
    assert agents.AgentRole.CONTRARIAN.value == "Contrarian"
    assert agents.AgentRole.FACT_CHECKER.value == "FactChecker"


@pytest.mark.integration
def test_package_metadata_exports() -> None:
    """Autoresearch top-level metadata should stay importable."""
    package = importlib.import_module("autoresearch")

    assert isinstance(package.__version__, str)
    assert package.__version__
    assert isinstance(package.__release_date__, str)
    assert package.__release_date__.count("-") == 2


@pytest.mark.integration
def test_cli_apps_are_exposed() -> None:
    """Ensure CLI entry points stay attached to the Typer application."""
    main_app = importlib.import_module("autoresearch.main.app")

    assert isinstance(main_app.app, Typer)
    assert isinstance(main_app.search_app, Typer)
    assert callable(main_app.search)
