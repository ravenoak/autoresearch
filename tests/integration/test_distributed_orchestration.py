from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import pytest

from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import ProcessExecutor
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager
from tests.integration._orchestrator_stubs import AgentDouble, AgentResultFactory, patch_agent_factory_get

pytestmark = pytest.mark.slow


def _claim_result_factory(
    agent_name: str,
    pid_log: list[int],
) -> AgentResultFactory:
    def build_payload(state: QueryState, config: ConfigModel) -> Mapping[str, object]:
        del config  # orchestration doubles ignore config content
        pid_log.append(os.getpid())
        claim = {"id": f"{agent_name}-1", "type": "fact", "content": agent_name}
        return {"results": {agent_name: "ok"}, "claims": [claim]}

    return build_payload


def _make_claim_agent(name: str, pid_log: list[int]) -> AgentDouble:
    return AgentDouble(name=name, result_factory=_claim_result_factory(name, pid_log))


def test_distributed_orchestration_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pids: list[int] = []
    agents = [_make_claim_agent(agent_name, pids) for agent_name in ("A", "B")]
    patch_agent_factory_get(monkeypatch, agents)
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
