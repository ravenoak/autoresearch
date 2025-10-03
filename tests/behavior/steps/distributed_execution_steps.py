"""Step definitions for distributed execution feature."""

from __future__ import annotations
from tests.behavior.utils import as_payload
from tests.behavior.context import BehaviorContext

import importlib.util
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

import pytest
from pytest_bdd import given, scenario, then, when

from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import ProcessExecutor, RayExecutor
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager


ExecutorClass: TypeAlias = type[ProcessExecutor] | type[RayExecutor]


@dataclass
class DistributedArtifacts:
    """Container for distributed execution state shared across steps."""

    config: ConfigModel
    executor_cls: ExecutorClass
    db_path: str
    response: QueryResponse | None = None
    pids: list[int] = field(default_factory=list)


def _get_distributed_artifacts(bdd_context: BehaviorContext) -> DistributedArtifacts:
    """Retrieve distributed execution artifacts from the behavior context."""

    artifacts = bdd_context.get("distributed")
    if not isinstance(artifacts, DistributedArtifacts):  # pragma: no cover - safety net
        raise AssertionError("Distributed artifacts not configured")
    return artifacts


# Scenarios
@pytest.mark.slow
@pytest.mark.requires_distributed
@scenario("../features/distributed_execution.feature", "Run distributed query with Ray executor")
def test_ray_executor(bdd_context: BehaviorContext):
    """Run distributed query with Ray executor."""
    pass


@pytest.mark.slow
@pytest.mark.requires_distributed
@scenario("../features/distributed_execution.feature", "Run distributed query with multiprocessing")
def test_process_executor(bdd_context: BehaviorContext):
    """Run distributed query with multiprocessing."""
    pass


# Fixtures and steps
@pytest.fixture
def pids() -> list[int]:
    return []


@given("mock agents that persist claims")
def mock_agents(monkeypatch: pytest.MonkeyPatch, pids: list[int]) -> None:
    class ClaimAgent:
        def __init__(self, name: str, pid_list: list[int]):
            self.name = name
            self._pids = pid_list

        def can_execute(self, state: QueryState, config: ConfigModel) -> bool:  # pragma: no cover - dummy
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
            return as_payload({"results": {self.name: "ok"}, "claims": [claim]})

    monkeypatch.setattr(AgentFactory, "get", lambda name: ClaimAgent(name, pids))


@given("a distributed configuration using Ray")
def config_ray(tmp_path: Path, bdd_context: BehaviorContext, pids: list[int]) -> None:
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
    bdd_context["distributed"] = DistributedArtifacts(
        config=cfg,
        executor_cls=RayExecutor,
        db_path=cfg.storage.duckdb_path,
        pids=pids,
    )


@given("a distributed configuration using multiprocessing")
def config_process(tmp_path: Path, bdd_context: BehaviorContext, pids: list[int]) -> None:
    if not os.getenv("ENABLE_DISTRIBUTED_TESTS"):
        pytest.skip("Distributed tests are disabled")
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2, message_broker="memory"),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )
    bdd_context["distributed"] = DistributedArtifacts(
        config=cfg,
        executor_cls=ProcessExecutor,
        db_path=cfg.storage.duckdb_path,
        pids=pids,
    )


@when("I run a distributed query")
def run_distributed_query(bdd_context: BehaviorContext) -> None:
    artifacts = _get_distributed_artifacts(bdd_context)
    executor = artifacts.executor_cls(artifacts.config)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"
    executor.shutdown()
    artifacts.response = resp


@then("the claims should be persisted for each agent")
def claims_persisted(bdd_context: BehaviorContext) -> None:
    artifacts = _get_distributed_artifacts(bdd_context)
    StorageManager.setup(artifacts.db_path)
    conn = StorageManager.get_duckdb_conn()
    rows = conn.execute("SELECT id FROM nodes ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["A", "B"]


@then("more than one process should execute")
def multiple_processes_used(bdd_context: BehaviorContext) -> None:
    artifacts = _get_distributed_artifacts(bdd_context)
    assert len(set(artifacts.pids)) > 1
