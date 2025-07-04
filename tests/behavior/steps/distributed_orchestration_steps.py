from __future__ import annotations

import os
import ray
import pytest
from pytest_bdd import scenario, given, when, then

from autoresearch.distributed import RayExecutor
from autoresearch.config import ConfigModel, DistributedConfig
from autoresearch.models import QueryResponse
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


@pytest.fixture
def context():
    return {}


@scenario("../features/distributed_orchestration.feature", "Running agents across processes")
def test_running_agents_across_processes():
    pass


@given("a distributed configuration with 2 workers")
def cfg(context):
    context["pids"] = []
    context["cfg"] = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    return context["cfg"]


@when("I execute a distributed query with two agents")
def run_query(cfg, context, monkeypatch):
    monkeypatch.setattr(AgentFactory, "get", lambda name: DummyAgent(name, context["pids"]))
    executor = RayExecutor(cfg)
    context["resp"] = executor.run_query("q")
    context["pool_size"] = executor.resource_pool.size
    executor.shutdown()
    ray.shutdown()


@then("multiple worker processes should be used")
def check_processes(context):
    assert context["pool_size"] == 2
    assert len(set(context["pids"])) > 1
    assert isinstance(context["resp"], QueryResponse)
