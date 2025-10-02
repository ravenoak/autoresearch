from __future__ import annotations

import os
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pytest
from prometheus_client import CollectorRegistry

from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch import search
from autoresearch.agents.registry import AgentFactory
from autoresearch.distributed import executors
from autoresearch.distributed.broker import (
    BrokerMessage,
    MessageQueueProtocol,
    StorageBrokerQueueProtocol,
)
from autoresearch.llm import pool as llm_pool
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState

from tests.integration._executor_stubs import patch_tracking_agent_factory
from tests.typing_helpers import TypedFixture

package = types.ModuleType("autoresearch.monitor")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "src" / "autoresearch" / "monitor")]
sys.modules.setdefault("autoresearch.monitor", package)
from autoresearch.monitor.node_health import NodeHealthMonitor  # noqa: E402

pytestmark = [pytest.mark.slow, pytest.mark.requires_distributed]


class _SessionSentinel:
    """Simple sentinel carrying a descriptive label for assertions."""

    def __init__(self, label: str) -> None:
        self.label = label


_HTTP_SESSION_SENTINEL: Final[_SessionSentinel] = _SessionSentinel("http")
_LLM_SESSION_SENTINEL: Final[_SessionSentinel] = _SessionSentinel("llm")


def _stub_http_session() -> _SessionSentinel:
    return _HTTP_SESSION_SENTINEL


def _stub_llm_session() -> _SessionSentinel:
    return _LLM_SESSION_SENTINEL


def _dummy_execute_agent_remote(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    result_queue: MessageQueueProtocol | None = None,
    storage_queue: StorageBrokerQueueProtocol | None = None,
    http_session: object | None = None,
    llm_session: object | None = None,
) -> BrokerMessage:
    if http_session is not None and isinstance(
        http_session, executors.ray.ObjectRef
    ):  # pragma: no cover - retrieval
        http_session = executors.ray.get(http_session)
    if llm_session is not None and isinstance(
        llm_session, executors.ray.ObjectRef
    ):  # pragma: no cover - retrieval
        llm_session = executors.ray.get(llm_session)
    agent = AgentFactory.get(agent_name)
    res = agent.execute(state, config)
    msg: BrokerMessage = {
        "action": "agent_result",
        "agent": agent_name,
        "result": res,
        "pid": os.getpid(),
    }
    result_queue_local: MessageQueueProtocol | None = result_queue
    if result_queue_local is not None:
        result_queue_local.put(msg)
    return msg


class DummyRemote:
    """Wrapper mirroring Ray's ``RemoteFunction`` callable interface."""

    def __init__(self, func: Callable[..., BrokerMessage] | None = None) -> None:
        self._func: Callable[..., BrokerMessage] = func or _dummy_execute_agent_remote

    def remote(
        self,
        agent_name: str,
        state: QueryState,
        config: ConfigModel,
        result_queue: MessageQueueProtocol | None = None,
        storage_queue: StorageBrokerQueueProtocol | None = None,
        http_session: object | None = None,
        llm_session: object | None = None,
    ) -> BrokerMessage:  # pragma: no cover - wrapper
        return self._func(
            agent_name,
            state,
            config,
            result_queue=result_queue,
            storage_queue=storage_queue,
            http_session=http_session,
            llm_session=llm_session,
        )


class DummyObjectRef:
    def __init__(self, obj: object) -> None:  # pragma: no cover - trivial
        self.obj = obj


class DummyRay(types.ModuleType):
    ObjectRef = DummyObjectRef

    def __init__(self) -> None:  # pragma: no cover - trivial
        super().__init__("ray")
        self._initialized = False

    def init(self, **_: object) -> None:
        self._initialized = True

    def is_initialized(self) -> bool:
        return self._initialized

    def shutdown(self) -> None:  # pragma: no cover - trivial
        self._initialized = False

    def get(self, obj: DummyObjectRef | object) -> object:  # pragma: no cover - trivial
        if isinstance(obj, DummyObjectRef):
            return obj.obj
        return obj

    def put(self, obj: object) -> DummyObjectRef:  # pragma: no cover - trivial
        return DummyObjectRef(obj)

    def remote(self, func: Callable[..., BrokerMessage]) -> DummyRemote:  # pragma: no cover - trivial
        return DummyRemote(func)

    def cluster_resources(self) -> dict[str, int]:  # pragma: no cover - trivial
        return {"CPU": 1}


@pytest.fixture
def dummy_ray(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[DummyRay]:
    ray_mod = DummyRay()
    monkeypatch.setitem(sys.modules, "ray", ray_mod)
    monkeypatch.setattr(executors, "ray", ray_mod)
    return ray_mod


def test_ray_executor(monkeypatch: pytest.MonkeyPatch, dummy_ray: DummyRay) -> None:
    pids: list[int] = []
    patch_tracking_agent_factory(monkeypatch, pids)
    monkeypatch.setattr(executors, "_execute_agent_remote", DummyRemote())
    monkeypatch.setattr(search, "get_http_session", _stub_http_session)
    monkeypatch.setattr(llm_pool, "get_session", _stub_llm_session)
    cfg: ConfigModel = ConfigModel(
        agents=["A"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=1),
    )
    executor = executors.RayExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    assert pids, "Agent should execute remotely"
    executor.shutdown()
    registry = CollectorRegistry()
    monitor = NodeHealthMonitor(ray_address="auto", port=None, interval=0.1, registry=registry)
    monitor.check_once()
    assert registry.get_sample_value("autoresearch_ray_up") == 1.0
    assert registry.get_sample_value("autoresearch_node_health") == 1.0
