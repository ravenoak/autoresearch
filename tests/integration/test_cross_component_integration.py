# mypy: ignore-errors
"""Cross-component integration tests."""

from __future__ import annotations

from typing import Any

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.config_utils import apply_preset
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.search.core import Search
from autoresearch.storage import StorageManager


class SearchAgent:
    """Agent that performs search and persists results."""

    def __init__(self, name: str, llm_adapter: Any | None = None) -> None:
        self.name = name

    def can_execute(self, state, config):  # pragma: no cover - simple stub
        return True

    def execute(self, state, config, **kwargs):  # pragma: no cover - simple stub
        results = Search.external_lookup(state.query, max_results=2)
        for r in results:
            StorageManager.persist_claim({"id": r["url"], "type": "source", "content": r["title"]})
        state.results["final_answer"] = "done"
        return {"results": {self.name: "ok"}}


@pytest.mark.slow
def test_preset_drives_cross_component_flow(monkeypatch):
    """Preset config enables orchestrator, search, and storage integration."""
    calls: list[str] = []
    stored: list[dict[str, str]] = []

    monkeypatch.setattr(
        Search,
        "external_lookup",
        lambda q, max_results=2: [{"title": "Doc1", "url": "u1"}],
    )
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim))

    class RecordingAgent(SearchAgent):
        def execute(self, state, config, **kwargs):
            calls.append(self.name)
            return super().execute(state, config, **kwargs)

    monkeypatch.setattr(AgentFactory, "get", lambda name: RecordingAgent(name))

    cfg_data = apply_preset("Default")
    cfg_data["agents"] = ["SearchAgent"]
    cfg = ConfigModel(**cfg_data)

    resp = Orchestrator().run_query("q", cfg)

    assert isinstance(resp, QueryResponse)
    assert resp.answer == "done"
    assert calls == ["SearchAgent"]
    assert stored == [{"id": "u1", "type": "source", "content": "Doc1"}]
