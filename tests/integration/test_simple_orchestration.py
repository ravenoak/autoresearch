from __future__ import annotations

from typing import Any

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.integration._orchestrator_stubs import (
    AgentDouble,
    PersistClaimCall,
    patch_agent_factory_get,
    patch_storage_persist,
)


def test_orchestrator_run_query(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    synthesizer = AgentDouble(name="Synthesizer")

    def result_factory(
        state: Any,
        config: ConfigModel,
        *,
        stub: AgentDouble = synthesizer,
    ) -> dict[str, Any]:
        original_factory = stub.result_factory
        stub.result_factory = None
        try:
            payload = stub._build_payload(state, config)
        finally:
            stub.result_factory = original_factory
        results_section = dict(payload.get("results", {}))
        results_section["final_answer"] = "Answer from Synthesizer"
        payload["results"] = results_section
        payload["answer"] = "Answer from Synthesizer"
        payload["sources"] = [
            {
                "id": "synthesizer-source",
                "type": "url",
                "value": "https://example.com/synthesizer",
            }
        ]
        return payload

    synthesizer.result_factory = result_factory
    synthesizer.call_log = calls
    patch_agent_factory_get(monkeypatch, [synthesizer])

    cfg = ConfigModel(agents=["Synthesizer"], loops=1)

    def load_config_override(self: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_override)
    ConfigLoader()._config = None

    response = Orchestrator().run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == ["Synthesizer"]
    assert response.answer == "Answer from Synthesizer"
