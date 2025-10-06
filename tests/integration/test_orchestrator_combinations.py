# mypy: ignore-errors
from __future__ import annotations

import itertools
from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.errors import OrchestrationError
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.token_utils import AdapterProtocol
from pytest import MonkeyPatch
from tests.integration._orchestrator_stubs import (
    AgentDouble,
    PersistClaimCall,
    patch_agent_factory_get,
    patch_storage_persist,
)


@pytest.mark.parametrize(
    "agents",
    list(itertools.permutations(["AgentA", "AgentB", "Synthesizer"])),
)
def test_orchestrator_agent_combinations(
    monkeypatch: MonkeyPatch,
    agents: tuple[str, ...],
) -> None:
    calls: list[str] = []
    search_calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    agent_doubles: list[AgentDouble] = []
    for agent_name in ["AgentA", "AgentB", "Synthesizer"]:
        double = AgentDouble(name=agent_name)

        def result_factory(
            state: QueryState,
            config: ConfigModel,
            *,
            name: str = agent_name,
            stub: AgentDouble = double,
        ) -> dict[str, object]:
            search_calls.append(name)
            original_factory = stub.result_factory
            stub.result_factory = None
            try:
                payload = stub._build_payload(state, config)
            finally:
                stub.result_factory = original_factory
            results_section = dict(payload.get("results", {}))
            if name == "Synthesizer":
                results_section["final_answer"] = "Answer from Synthesizer"
                payload["answer"] = "Answer from Synthesizer"
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
        metrics: OrchestrationMetrics,
        config: ConfigModel,
    ) -> Iterator[tuple[dict[str, int], AdapterProtocol]]:
        del agent_name, metrics, config

        class _Adapter:
            def generate(
                self, prompt: str, model: str | None = None, **kwargs: object
            ) -> str:
                del prompt, model, kwargs
                return ""

        yield ({}, cast(AdapterProtocol, _Adapter()))

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    agent_list: list[str] = list(agents)
    cfg: ConfigModel = ConfigModel(agents=agent_list, loops=1)
    response = Orchestrator().run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == agent_list
    assert search_calls == calls
    expected_claim_ids = [f"{agent.lower()}-claim" for agent in agents]
    assert [call.claim["id"] for call in persist_calls] == expected_claim_ids
    assert response.answer == "Answer from Synthesizer"


@pytest.mark.parametrize(
    "agents",
    list(itertools.permutations(["AgentA", "AgentB", "Synthesizer"], 2)),
)
def test_orchestrator_agent_pairings(
    monkeypatch: MonkeyPatch,
    agents: tuple[str, ...],
) -> None:
    calls: list[str] = []
    search_calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    agent_doubles: list[AgentDouble] = []
    for agent_name in ["AgentA", "AgentB", "Synthesizer"]:
        double = AgentDouble(name=agent_name)

        def result_factory(
            state: QueryState,
            config: ConfigModel,
            *,
            name: str = agent_name,
            stub: AgentDouble = double,
        ) -> dict[str, object]:
            search_calls.append(name)
            original_factory = stub.result_factory
            stub.result_factory = None
            try:
                payload = stub._build_payload(state, config)
            finally:
                stub.result_factory = original_factory
            results_section = dict(payload.get("results", {}))
            if name == "Synthesizer":
                results_section["final_answer"] = "Answer from Synthesizer"
                payload["answer"] = "Answer from Synthesizer"
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
        metrics: OrchestrationMetrics,
        config: ConfigModel,
    ) -> Iterator[tuple[dict[str, int], AdapterProtocol]]:
        del agent_name, metrics, config

        class _Adapter:
            def generate(
                self, prompt: str, model: str | None = None, **kwargs: object
            ) -> str:
                del prompt, model, kwargs
                return ""

        yield ({}, cast(AdapterProtocol, _Adapter()))

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    agent_list: list[str] = list(agents)
    cfg: ConfigModel = ConfigModel(agents=agent_list, loops=1)
    response = Orchestrator().run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == agent_list
    assert search_calls == calls
    expected_claim_ids = [f"{agent.lower()}-claim" for agent in agents]
    assert [call.claim["id"] for call in persist_calls] == expected_claim_ids
    expected_answer = (
        "Answer from Synthesizer" if "Synthesizer" in agents else "No answer synthesized"
    )
    assert response.answer == expected_answer


pairings: list[tuple[str, str]] = list(
    itertools.permutations(["AgentA", "AgentB", "Synthesizer"], 2)
)


@pytest.mark.slow
@pytest.mark.parametrize(
    "agents, fail_index",
    [(p, i) for p in pairings for i in range(len(p))],
)
def test_orchestrator_failure_modes(
    monkeypatch: MonkeyPatch,
    agents: tuple[str, ...],
    fail_index: int,
) -> None:
    calls: list[str] = []
    search_calls: list[str] = []
    persist_calls: list[PersistClaimCall] = []
    patch_storage_persist(monkeypatch, persist_calls)

    failing_agent = agents[fail_index]

    agent_doubles: list[AgentDouble] = []
    for agent_name in ["AgentA", "AgentB", "Synthesizer"]:
        error: RuntimeError | None = None
        if agent_name == failing_agent:
            error = RuntimeError(f"{agent_name} failed")

        double = AgentDouble(name=agent_name, error=error)

        def result_factory(
            state: QueryState,
            config: ConfigModel,
            *,
            name: str = agent_name,
            stub: AgentDouble = double,
        ) -> dict[str, object]:
            search_calls.append(name)
            original_factory = stub.result_factory
            stub.result_factory = None
            try:
                payload = stub._build_payload(state, config)
            finally:
                stub.result_factory = original_factory
            results_section = dict(payload.get("results", {}))
            if name == "Synthesizer":
                results_section["final_answer"] = "Answer from Synthesizer"
                payload["answer"] = "Answer from Synthesizer"
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
        metrics: OrchestrationMetrics,
        config: ConfigModel,
    ) -> Iterator[tuple[dict[str, int], AdapterProtocol]]:
        del agent_name, metrics, config

        class _Adapter:
            def generate(
                self, prompt: str, model: str | None = None, **kwargs: object
            ) -> str:
                del prompt, model, kwargs
                return ""

        yield ({}, cast(AdapterProtocol, _Adapter()))

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    agent_list: list[str] = list(agents)
    cfg: ConfigModel = ConfigModel(agents=agent_list, loops=1, max_errors=1)
    with pytest.raises(OrchestrationError):
        Orchestrator().run_query("q", cfg)

    failing_agent = agents[fail_index]
    if failing_agent == "Synthesizer":
        if fail_index == 0:
            expected_calls = []
        else:
            expected_calls = [a for a in agents if a != "Synthesizer"]
    else:
        expected_calls = []
        for a in agents:
            if a == failing_agent:
                break
            if a != "Synthesizer":
                expected_calls.append(a)

    assert calls == expected_calls
    assert search_calls == calls
    expected_claim_ids = [f"{agent.lower()}-claim" for agent in calls]
    assert [call.claim["id"] for call in persist_calls] == expected_claim_ids
