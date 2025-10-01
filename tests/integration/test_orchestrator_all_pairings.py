from __future__ import annotations

import itertools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest

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


pairs: list[tuple[str, str]] = list(
    itertools.permutations(["AgentA", "AgentB", "AgentC", "Synthesizer"], 2)
)


@pytest.mark.slow
@pytest.mark.parametrize("agents", pairs)
def test_orchestrator_all_agent_pairings(
    monkeypatch: MonkeyPatch,
    agents: tuple[str, str],
) -> None:
    calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    agent_doubles: list[AgentDouble] = []
    for agent_name in ["AgentA", "AgentB", "AgentC", "Synthesizer"]:
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

        double.result_factory = result_factory
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
    expected_claim_ids = [f"{agent.lower()}-claim" for agent in agent_list]
    assert [call.claim["id"] for call in persist_calls] == expected_claim_ids
    expected = "Answer from Synthesizer" if "Synthesizer" in agents else "No answer synthesized"
    assert response.answer == expected
