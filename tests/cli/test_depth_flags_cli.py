"""CLI integration tests for depth-aware output flags."""

from __future__ import annotations

import importlib
import json
from typing import Any

import pytest
from typer.testing import CliRunner

from autoresearch.models import QueryResponse

pytestmark = pytest.mark.usefixtures("dummy_storage")


def _main():
    return importlib.import_module("autoresearch.main")


def _app_mod():
    return importlib.import_module("autoresearch.main.app")


class _DummyOrchestrator:
    """Minimal orchestrator stub returning deterministic responses."""

    def run_query(
        self,
        query: str,
        config: Any,
        callbacks: Any | None = None,
        *,
        agent_factory: Any | None = None,
        storage_manager: Any | None = None,
        visualize: bool = False,
    ) -> QueryResponse:
        return QueryResponse(
            answer="Depth-enabled answer.",
            citations=["Doc A"],
            reasoning=[{"id": "1", "type": "claim", "content": "Claim body"}],
            metrics={"tldr": "Brief summary", "audit": {"steps": [{"agent": "Synth"}]}},
        )


def test_depth_flags_markdown(monkeypatch, config_loader):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(_app_mod(), "_config_loader", config_loader)
    monkeypatch.setattr(_app_mod(), "Orchestrator", _DummyOrchestrator)

    result = runner.invoke(
        _main().app,
        [
            "search",
            "example",
            "--depth",
            "tldr",
            "--depth",
            "claims",
            "--depth",
            "trace",
        ],
    )

    assert result.exit_code == 0
    assert "## TL;DR" in result.stdout
    assert "Claim body" in result.stdout
    assert "Trace" in result.stdout


def test_depth_flags_json(monkeypatch, config_loader):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(_app_mod(), "_config_loader", config_loader)
    monkeypatch.setattr(_app_mod(), "Orchestrator", _DummyOrchestrator)

    result = runner.invoke(
        _main().app,
        ["search", "example", "--output", "json", "--depth", "tldr"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["depth_sections"]["tldr"] == "Brief summary"
