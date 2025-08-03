import itertools

import pytest

from contextlib import contextmanager

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.models import QueryResponse
from autoresearch.errors import OrchestrationError


def make_agent(name, calls, search_calls, store_calls, *, fail=False):
    class DummyAgent:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config, **kwargs):
            if fail:
                raise RuntimeError(f"{self.name} failed")
            Search.rank_results(
                "q", [{"title": "t", "url": "https://example.com"}]
            )
            StorageManager.persist_claim(
                {"id": self.name, "type": "fact", "content": self.name}
            )
            calls.append(self.name)
            search_calls.append(self.name)
            state.update(
                {
                    "results": {self.name: "ok"},
                    "claims": [
                        {
                            "id": self.name,
                            "type": "fact",
                            "content": self.name,
                        }
                    ],
                }
            )
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {"results": {self.name: "ok"}}

    return DummyAgent(name)


@pytest.mark.parametrize(
    "agents",
    list(itertools.permutations(["AgentA", "AgentB", "Synthesizer"])),
)
def test_orchestrator_agent_combinations(monkeypatch, agents):
    calls: list[str] = []
    search_calls: list[str] = []
    store_calls: list[dict] = []
    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: store_calls.append(claim)
    )
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name, llm_adapter=None: make_agent(
            name, calls, search_calls, store_calls
        ),
    )

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(
        Orchestrator, "_capture_token_usage", no_token_capture
    )

    cfg = ConfigModel(agents=list(agents), loops=1)
    response = Orchestrator.run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == list(agents)
    assert search_calls == calls
    expected_claims = [
        {"id": a, "type": "fact", "content": a} for a in agents
    ]
    assert store_calls == expected_claims
    assert response.answer == "Answer from Synthesizer"


@pytest.mark.parametrize(
    "agents",
    list(itertools.permutations(["AgentA", "AgentB", "Synthesizer"], 2)),
)
def test_orchestrator_agent_pairings(monkeypatch, agents):
    calls: list[str] = []
    search_calls: list[str] = []
    store_calls: list[dict] = []
    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: store_calls.append(claim)
    )
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name, llm_adapter=None: make_agent(
            name, calls, search_calls, store_calls
        ),
    )

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(
        Orchestrator, "_capture_token_usage", no_token_capture
    )

    cfg = ConfigModel(agents=list(agents), loops=1)
    response = Orchestrator.run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == list(agents)
    assert search_calls == calls
    expected_claims = [
        {"id": a, "type": "fact", "content": a} for a in agents
    ]
    assert store_calls == expected_claims
    expected_answer = (
        "Answer from Synthesizer" if "Synthesizer" in agents else "No answer synthesized"
    )
    assert response.answer == expected_answer


pairings = list(itertools.permutations(["AgentA", "AgentB", "Synthesizer"], 2))


@pytest.mark.parametrize(
    "agents, fail_index",
    [(p, i) for p in pairings for i in range(len(p))],
)
def test_orchestrator_failure_modes(monkeypatch, agents, fail_index):
    calls: list[str] = []
    search_calls: list[str] = []
    store_calls: list[dict] = []
    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: store_calls.append(claim)
    )
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name, llm_adapter=None: make_agent(
            name,
            calls,
            search_calls,
            store_calls,
            fail=(name == agents[fail_index]),
        ),
    )

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(
        Orchestrator, "_capture_token_usage", no_token_capture
    )

    cfg = ConfigModel(agents=list(agents), loops=1, max_errors=1)
    with pytest.raises(OrchestrationError):
        Orchestrator.run_query("q", cfg)

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
    expected_claims = [{"id": a, "type": "fact", "content": a} for a in calls]
    assert store_calls == expected_claims
