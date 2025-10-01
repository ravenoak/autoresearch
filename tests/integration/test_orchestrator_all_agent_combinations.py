from __future__ import annotations

import itertools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import orchestrator as orch_mod
from pytest import MonkeyPatch
from tests.integration._orchestrator_stubs import (
    AgentDouble,
    PersistClaimCall,
    patch_agent_factory_get,
    patch_storage_persist,
)

Orchestrator = orch_mod.Orchestrator


pytestmark = pytest.mark.integration

AGENTS: list[str] = ["AgentA", "AgentB", "AgentC", "Synthesizer"]


def all_permutations() -> Iterator[tuple[str, ...]]:
    for r in range(1, len(AGENTS) + 1):
        yield from itertools.permutations(AGENTS, r)


@pytest.mark.parametrize("agents", list(all_permutations()))
def test_orchestrator_all_agent_combinations(
    monkeypatch: MonkeyPatch,
    agents: tuple[str, ...],
) -> None:
    calls: list[str] = []
    search_calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    agent_doubles: list[AgentDouble] = []
    for agent_name in AGENTS:
        double = AgentDouble(name=agent_name)

        def build_result(
            state: Any,
            config: ConfigModel,
            *,
            name: str = agent_name,
            stub: AgentDouble = double,
        ) -> dict[str, Any]:
            search_calls.append(name)
            original_factory = stub.result_factory
            stub.result_factory = None
            try:
                payload = stub._build_payload(state, config)
            finally:
                stub.result_factory = original_factory
            results_section = dict(payload.get("results", {}))
            if name == "Synthesizer":
                results_section["final_answer"] = f"Answer from {name}"
                payload["answer"] = f"Answer from {name}"
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

        double.result_factory = build_result
        double.call_log = calls
        agent_doubles.append(double)

    patch_agent_factory_get(monkeypatch, agent_doubles)

    @contextmanager
    def no_token_capture(
        agent_name: str,
        metrics: Any,
        config: ConfigModel,
    ) -> Iterator[tuple[Callable[..., None], None]]:
        del agent_name, metrics, config
        yield (lambda *args, **kwargs: None, None)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    agent_list: list[str] = list(agents)
    cfg: ConfigModel = ConfigModel(agents=agent_list, loops=1)
    response = Orchestrator().run_query("q", cfg)

    assert isinstance(response, QueryResponse)
    assert calls == agent_list
    assert search_calls == agent_list
    expected_claim_ids = [f"{agent.lower()}-claim" for agent in agent_list]
    assert [call.claim["id"] for call in persist_calls] == expected_claim_ids
    expected = (
        "Answer from Synthesizer"
        if "Synthesizer" in agents
        else "No answer synthesized"
    )
    assert response.answer == expected
