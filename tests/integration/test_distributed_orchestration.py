import os
import pytest
from autoresearch.distributed import ProcessExecutor
from autoresearch.config import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager

pytestmark = pytest.mark.slow


class ClaimAgent:
    def __init__(self, name: str, pids: list[int]):
        self.name = name
        self._pids = pids

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:  # pragma: no cover - dummy
        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> dict:
        self._pids.append(os.getpid())
        claim = {"id": f"{self.name}-1", "type": "fact", "content": self.name}
        state.update({"results": {self.name: "ok"}, "claims": [claim]})
        return {"results": {self.name: "ok"}, "claims": [claim]}


def test_distributed_orchestration_persistence(tmp_path, monkeypatch):
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: ClaimAgent(name, pids))
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2, message_broker="memory"),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    executor = ProcessExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    executor.shutdown()

    StorageManager.setup(str(tmp_path / "kg.duckdb"))
    conn = StorageManager.get_duckdb_conn()
    rows = conn.execute("SELECT id FROM nodes ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["A-1", "B-1"]
    assert len(set(pids)) > 1
