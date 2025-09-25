import concurrent.futures
from typing import List, Tuple

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import orchestrator as orch_mod

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory


def _make_echo_agent(name: str, calls: List[Tuple[str, str, int]]):
    class EchoAgent:
        def __init__(self, name: str, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config, **kwargs):
            calls.append((self.name, state.query, id(state)))
            state.results["final_answer"] = f"Echo: {state.query}"
            return {"results": {self.name: state.query}}

    return EchoAgent(name)


def test_parallel_queries_isolate_state(monkeypatch):
    calls: List[Tuple[str, str, int]] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_echo_agent(name, calls))

    def run_query(q: str):
        cfg = ConfigModel(agents=["Echo"], loops=1)
        return Orchestrator().run_query(q, cfg)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(run_query, "q1")
        f2 = pool.submit(run_query, "q2")
        r1 = f1.result()
        r2 = f2.result()

    assert {c[0:2] for c in calls} == {("Echo", "q1"), ("Echo", "q2")}
    ids = {c[2] for c in calls}
    assert len(ids) == 2
    assert r1.answer == "Echo: q1"
    assert r2.answer == "Echo: q2"
