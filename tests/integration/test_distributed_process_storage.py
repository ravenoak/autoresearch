import os
import pytest
from autoresearch.distributed import ProcessExecutor
from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.storage import StorageManager
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState

pytestmark = pytest.mark.slow


class ClaimAgent:
    def __init__(self, name: str, pids: list[int]):
        self.name = name
        self._pids = pids

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:  # pragma: no cover - dummy
        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> dict:
        self._pids.append(os.getpid())
        StorageManager.persist_claim({"id": self.name, "type": "fact", "content": "x"})
        state.update({"results": {self.name: "ok"}})
        return {"results": {self.name: "ok"}}


def test_process_storage_with_executor(tmp_path, monkeypatch):
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: ClaimAgent(name, pids))
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    executor = ProcessExecutor(cfg)
    executor.run_query("q")
    assert len(set(pids)) > 1
    executor.shutdown()
    StorageManager.setup(str(tmp_path / "kg.duckdb"))
    conn = StorageManager.get_duckdb_conn()
    rows = conn.execute("SELECT id FROM nodes ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["A", "B"]
