# mypy: ignore-errors
from __future__ import annotations

import os
from typing import Mapping

import pytest
import ray

from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch.distributed import RayExecutor, ResultAggregator
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState
from tests.integration._orchestrator_stubs import AgentDouble, AgentResultFactory, patch_agent_factory_get

pytestmark = pytest.mark.slow


def _result_factory(
    agent_name: str,
    pid_log: list[int],
) -> AgentResultFactory:
    def build_payload(state: QueryState, config: ConfigModel) -> Mapping[str, object]:
        del config  # orchestration doubles ignore config content
        pid_log.append(os.getpid())
        return {"results": {agent_name: "ok"}}

    return build_payload


def _make_agent(name: str, pid_log: list[int]) -> AgentDouble:
    return AgentDouble(name=name, result_factory=_result_factory(name, pid_log))


def test_result_aggregation_multi_process(monkeypatch: pytest.MonkeyPatch) -> None:
    pids: list[int] = []
    agents = [_make_agent(agent_name, pids) for agent_name in ("A", "B")]
    patch_agent_factory_get(monkeypatch, agents)
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    executor = RayExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    assert len(set(pids)) > 1
    aggregator: ResultAggregator | None = executor.result_aggregator
    assert aggregator is not None
    assert len(aggregator.results) == len(cfg.agents)
    os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"
    executor.shutdown()
    ray.shutdown()
