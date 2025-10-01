from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch

import autoresearch.orchestration.orchestrator as orchestrator_module
from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import ProcessExecutor
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.storage_typing import JSONDict

pytestmark = pytest.mark.slow


class ClaimAgent:
    def __init__(self, name: str, pids: list[int]):
        self.name = name
        self._pids = pids

    def can_execute(
        self, state: QueryState, config: ConfigModel
    ) -> bool:  # pragma: no cover - dummy
        return True

    def execute(
        self, state: QueryState, config: ConfigModel, **_: Any
    ) -> JSONDict:
        self._pids.append(os.getpid())
        claim: JSONDict = {"id": self.name, "type": "fact", "content": "x"}
        StorageManager.persist_claim(claim)
        state.update({"results": {self.name: "ok"}})
        return {"results": {self.name: "ok"}}


def test_process_storage_with_executor(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    pids: list[int] = []

    def agent_factory(name: str) -> ClaimAgent:
        return ClaimAgent(name, pids)

    monkeypatch.setattr(AgentFactoryClass, "get", agent_factory)
    cfg: ConfigModel = ConfigModel(
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

    context: StorageContext = StorageContext()
    state: StorageState = StorageState(context=context)
    StorageManager.setup(str(tmp_path / "kg.duckdb"), context=context, state=state)
    try:
        conn = StorageManager.get_duckdb_conn()
        rows: list[tuple[str]] = conn.execute(
            "SELECT id FROM nodes ORDER BY id"
        ).fetchall()
    finally:
        StorageManager.teardown(remove_db=True, context=context, state=state)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()

    assert [row[0] for row in rows] == ["A", "B"]
AgentFactoryClass = getattr(orchestrator_module, "AgentFactory")
