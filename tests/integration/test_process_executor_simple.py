import os

import pytest

from autoresearch.distributed import ProcessExecutor
from autoresearch.config import ConfigModel, DistributedConfig
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState
from autoresearch.models import QueryResponse


class DummyAgent:
    def __init__(self, name, pids):
        self.name = name
        self._pids = pids

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> dict:
        self._pids.append(os.getpid())
        state.update({"results": {self.name: "ok"}})
        return {"results": {self.name: "ok"}}


@pytest.mark.integration
def test_process_executor_runs(monkeypatch):
    pids = []
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
