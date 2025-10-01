"""Step definitions for distributed execution feature."""

import os
import importlib.util

import pytest
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, TypeAlias, cast

import pytest
from pytest_bdd import given, scenario, then, when

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import ProcessExecutor, RayExecutor
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager
from tests.behavior.context import BehaviorContext, set_value
from tests.typing_helpers import TypedFixture


# Scenarios
@pytest.mark.slow
@pytest.mark.requires_distributed
@scenario("../features/distributed_execution.feature", "Run distributed query with Ray executor")
def test_ray_executor(bdd_context: BehaviorContext) -> None:
    """Run distributed query with Ray executor."""


@pytest.mark.slow
@pytest.mark.requires_distributed
@scenario("../features/distributed_execution.feature", "Run distributed query with multiprocessing")
def test_process_executor(bdd_context: BehaviorContext) -> None:
    """Run distributed query with multiprocessing."""


# Fixtures and steps
@pytest.fixture
def pids(bdd_context: BehaviorContext) -> TypedFixture[list[int]]:
    """Capture process identifiers recorded by mock agents."""

    pid_list: list[int] = []
    set_value(bdd_context, "pids", pid_list)
    return pid_list


@given("mock agents that persist claims")
def mock_agents(monkeypatch: pytest.MonkeyPatch, pids: list[int]) -> None:
    """Register in-memory agents that persist claims during execution."""

    class ClaimAgent:
        def __init__(self, name: str, pid_list: list[int]) -> None:
            self.name = name
            self._pids = pid_list

        def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
            return True

        def execute(
            self,
            state: QueryState,
            config: ConfigModel,
            **_: object,
        ) -> dict[str, Any]:
            self._pids.append(os.getpid())
            claim = {"id": self.name, "type": "fact", "content": self.name}
            StorageManager.persist_claim(claim)
            state.update({"results": {self.name: "ok"}, "claims": [claim]})
            return {"results": {self.name: "ok"}, "claims": [claim]}

    monkeypatch.setattr(AgentFactory, "get", lambda name: ClaimAgent(name, pids))


@given("a distributed configuration using Ray")
def config_ray(
    tmp_path: Path,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configure the scenario to use the Ray executor when available."""

    if importlib.util.find_spec("ray") is None:
        pytest.skip("Ray not installed")
    if not os.getenv("ENABLE_DISTRIBUTED_TESTS"):
        pytest.skip("Distributed tests are disabled")
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2, message_broker="memory"),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    # Ensure required ray APIs exist in the test stub
    import ray as ray_module
    if not hasattr(ray_module, "put"):
        pytest.skip("Ray not available in test environment")
    set_value(bdd_context, "cfg", cfg)
    set_value(bdd_context, "executor_cls", RayExecutor)
    set_value(bdd_context, "db_path", cfg.storage.duckdb_path)


@given("a distributed configuration using multiprocessing")
def config_process(tmp_path: Path, bdd_context: BehaviorContext) -> None:
    """Configure the scenario to use the multiprocessing executor."""

    if not os.getenv("ENABLE_DISTRIBUTED_TESTS"):
        pytest.skip("Distributed tests are disabled")
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2, message_broker="memory"),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    set_value(bdd_context, "cfg", cfg)
    set_value(bdd_context, "executor_cls", ProcessExecutor)
    set_value(bdd_context, "db_path", cfg.storage.duckdb_path)


@when("I run a distributed query")
def run_distributed_query(bdd_context: BehaviorContext) -> None:
    """Execute the configured distributed query and capture the response."""

    cfg = cast(ConfigModel, bdd_context["cfg"])
    executor_cls = cast(ExecutorClass, bdd_context["executor_cls"])
    executor = executor_cls(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"
    executor.shutdown()
    bdd_context["response"] = resp


@then("the claims should be persisted for each agent")
def claims_persisted(bdd_context: BehaviorContext) -> None:
    """Verify persisted claims exist for each participating agent."""

    StorageManager.setup(cast(str, bdd_context["db_path"]))
    conn = StorageManager.get_duckdb_conn()
    rows = conn.execute("SELECT id FROM nodes ORDER BY id").fetchall()
    assert [row[0] for row in rows] == ["A", "B"]


@then("more than one process should execute")
def multiple_processes_used(bdd_context: BehaviorContext) -> None:
    """Ensure the distributed run touched more than one worker process."""

    pids = cast(list[int], bdd_context.get("pids", []))
    assert len(set(pids)) > 1
ExecutorClass: TypeAlias = type[ProcessExecutor] | type[RayExecutor]

