# mypy: ignore-errors
import os
from pathlib import Path

import pytest
import ray

from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import RayExecutor
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager
from autoresearch.storage_typing import JSONDict

pytestmark = pytest.mark.slow


class ClaimAgent:
    def __init__(self, name: str, pids: list[int]):
        self.name = name
        self._pids = pids

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:  # pragma: no cover - dummy
        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> JSONDict:
        self._pids.append(os.getpid())
        claim: JSONDict = {"id": self.name, "type": "fact", "content": "x"}
        StorageManager.persist_claim(claim)
        result: JSONDict = {"results": {self.name: "ok"}}
        state.update(result)
        return result


def test_distributed_storage_with_executor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: ClaimAgent(name, pids))
    cfg: ConfigModel = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    executor = RayExecutor(cfg)
    executor.run_query("q")
    assert len(set(pids)) > 1
    os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"
    executor.shutdown()
    StorageManager.setup(str(tmp_path / "kg.duckdb"))
    conn = StorageManager.get_duckdb_conn()
    rows = conn.execute("SELECT id FROM nodes ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["A", "B"]
    ray.shutdown()
