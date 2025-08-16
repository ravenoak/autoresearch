import itertools
from contextlib import contextmanager

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import orchestrator as orch_mod

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory
StorageManager = orch_mod.StorageManager


class Search:
    @staticmethod
    def rank_results(q, results):  # pragma: no cover - simple stub
        return results


pytestmark = pytest.mark.integration

AGENTS = ["AgentA", "AgentB", "AgentC", "Synthesizer"]


def make_agent(name, calls, search_calls):
    class DummyAgent:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):  # pragma: no cover - dummy
            return True

        def execute(self, state, config, **kwargs):  # pragma: no cover - dummy
            Search.rank_results("q", [{"title": "t", "url": "u"}])
            StorageManager.persist_claim(
                {"id": self.name, "type": "fact", "content": self.name}
            )
            calls.append(self.name)
            search_calls.append(self.name)
            state.results[self.name] = "ok"
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {"results": {self.name: "ok"}}

    return DummyAgent(name)


def all_permutations():
    for r in range(1, len(AGENTS) + 1):
        yield from itertools.permutations(AGENTS, r)


@pytest.mark.parametrize("agents", list(all_permutations()))
def test_orchestrator_all_agent_combinations(monkeypatch, agents):
    calls: list[str] = []
    search_calls: list[str] = []
    store_calls: list[str] = []
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: store_calls.append(claim["id"])
    )
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name, llm_adapter=None: make_agent(name, calls, search_calls),
    )

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    cfg = ConfigModel(agents=list(agents), loops=1)
    response = Orchestrator().run_query("q", cfg)

    assert isinstance(response, QueryResponse)
    assert calls == list(agents)
    assert search_calls == list(agents)
    assert store_calls == list(agents)
    expected = (
        "Answer from Synthesizer"
        if "Synthesizer" in agents
        else "No answer synthesized"
    )
    assert response.answer == expected
