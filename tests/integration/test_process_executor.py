import os
import pytest
from autoresearch.distributed import ProcessExecutor
from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState

pytestmark = pytest.mark.slow


class DummyAgent:
    def __init__(self, name: str, pids: list[int]):
        self.name = name
        self._pids = pids

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:  # pragma: no cover - dummy
        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> dict:
        self._pids.append(os.getpid())
        state.update({"results": {self.name: "ok"}})
        return {"results": {self.name: "ok"}}


def test_process_executor_multi_process(monkeypatch):
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: DummyAgent(name, pids))
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    executor = ProcessExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    assert len(set(pids)) > 1
    executor.shutdown()


def test_process_result_aggregation(monkeypatch):
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: DummyAgent(name, pids))
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    executor = ProcessExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    assert len(set(pids)) > 1
    assert executor.result_aggregator is not None
    assert len(executor.result_aggregator.results) == len(cfg.agents)
    executor.shutdown()
