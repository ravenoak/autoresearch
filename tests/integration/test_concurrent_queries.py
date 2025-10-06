# mypy: ignore-errors
import concurrent.futures
from dataclasses import dataclass, field
from typing import Tuple

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import orchestrator as orch_mod
from autoresearch.orchestration.state import QueryState
import pytest

from tests.integration._orchestrator_stubs import AgentDouble, patch_agent_factory_get

Orchestrator = orch_mod.Orchestrator


@dataclass(slots=True)
class EchoAgentDouble(AgentDouble):
    calls: list[Tuple[str, str, int]] = field(default_factory=list)

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        **_: object,
    ) -> dict[str, object]:
        record = (self.name, state.query, id(state))
        self.calls.append(record)
        payload = {
            "results": {self.name: state.query},
            "answer": f"Echo: {state.query}",
        }
        state.update(payload)
        state.results["final_answer"] = f"Echo: {state.query}"
        return payload


def _install_echo_agents(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[Tuple[str, str, int]],
) -> None:
    agent = EchoAgentDouble(name="Echo", calls=calls)
    patch_agent_factory_get(monkeypatch, (agent,))


def test_parallel_queries_isolate_state(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Tuple[str, str, int]] = []
    _install_echo_agents(monkeypatch, calls)

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
