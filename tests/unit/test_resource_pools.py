import os
from autoresearch.distributed import ProcessExecutor
from autoresearch.resource_pools import close_process_pool
from autoresearch.search import Search
from autoresearch.config import ConfigModel, DistributedConfig
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState


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


def test_http_session_reuse():
    Search.close_http_session()
    session1 = Search.get_http_session()
    session2 = Search.get_http_session()
    assert session1 is session2
    Search.close_http_session()


def test_process_pool_reuse(monkeypatch):
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: DummyAgent(name, pids))
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    executor = ProcessExecutor(cfg)
    executor.run_query("q")
    first = set(pids)
    pids.clear()
    executor.run_query("q")
    second = set(pids)
    assert first == second
    executor.shutdown()
    close_process_pool()
