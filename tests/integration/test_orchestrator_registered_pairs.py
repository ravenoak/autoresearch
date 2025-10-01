from __future__ import annotations

import itertools
from typing import Any

import pytest

from autoresearch.agents.registry import AgentRegistry
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from pytest import MonkeyPatch
from tests.integration._orchestrator_stubs import (
    AgentDouble,
    PersistClaimCall,
    patch_agent_factory_get,
    patch_storage_persist,
)


@pytest.mark.parametrize(
    "pair",
    list(itertools.combinations(AgentRegistry.list_available(), 2)),
)
def test_orchestrator_all_registered_pairs(
    monkeypatch: MonkeyPatch,
    pair: tuple[str, str],
) -> None:
    """Run the orchestrator with every pair of registered agents."""

    # Setup
    calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    agent_list: list[str] = list(pair)

    agent_doubles: list[AgentDouble] = []
    for agent_name in agent_list:
        double = AgentDouble(name=agent_name)

        def result_factory(
            state: Any,
            config: ConfigModel,
            *,
            name: str = agent_name,
            stub: AgentDouble = double,
        ) -> dict[str, Any]:
            original_factory = stub.result_factory
            stub.result_factory = None
            try:
                payload = stub._build_payload(state, config)
            finally:
                stub.result_factory = original_factory
            results_section = dict(payload.get("results", {}))
            if name == agent_list[-1]:
                results_section["final_answer"] = f"answer from {name}"
                payload["answer"] = f"answer from {name}"
            payload["results"] = results_section
            sources_section = payload.get("sources")
            if not isinstance(sources_section, list) or not sources_section:
                payload["sources"] = [
                    {
                        "id": f"{name.lower()}-source",
                        "type": "url",
                        "value": f"https://example.com/{name.lower()}",
                    }
                ]
            return payload

        double.result_factory = result_factory
        double.call_log = calls
        agent_doubles.append(double)

    patch_agent_factory_get(monkeypatch, agent_doubles)

    cfg: ConfigModel = ConfigModel(agents=agent_list, loops=1)

    # Execute
    response = Orchestrator().run_query("q", cfg)

    # Verify
    assert isinstance(response, QueryResponse)
    assert calls == agent_list
    assert response.answer == f"answer from {agent_list[-1]}"
