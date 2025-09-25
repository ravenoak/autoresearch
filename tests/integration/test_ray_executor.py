import os
import sys
import types
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry

from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch.distributed import executors
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory
from autoresearch.orchestration.state import QueryState

package = types.ModuleType("autoresearch.monitor")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "src" / "autoresearch" / "monitor")]
sys.modules.setdefault("autoresearch.monitor", package)
from autoresearch.monitor.node_health import NodeHealthMonitor  # noqa: E402

pytestmark = [pytest.mark.slow, pytest.mark.requires_distributed]


class DummyAgent:
    def __init__(self, name: str, pids: list[int]):
        self.name = name
        self._pids = pids

    def can_execute(
        self, state: QueryState, config: ConfigModel
    ) -> bool:  # pragma: no cover - stub
        return True

    def execute(self, state: QueryState, config: ConfigModel, **_: object) -> dict:
        self._pids.append(os.getpid())
        state.update({"results": {self.name: "ok"}})
        return {"results": {self.name: "ok"}}


def _dummy_execute_agent_remote(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    result_queue=None,
    storage_queue=None,
    http_session=None,
    llm_session=None,
):
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
    msg = {
        "action": "agent_result",
        "agent": agent_name,
        "result": res,
        "pid": os.getpid(),
    }
    if result_queue is not None:
        result_queue.put(msg)
    return msg


class DummyRemote:
    def remote(self, *args, **kwargs):  # pragma: no cover - wrapper
        return _dummy_execute_agent_remote(*args, **kwargs)


class DummyObjectRef:
    def __init__(self, obj):  # pragma: no cover - trivial
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

    def get(self, obj):  # pragma: no cover - trivial
        return obj

    def put(self, obj):  # pragma: no cover - trivial
        return DummyObjectRef(obj)

    def remote(self, func):  # pragma: no cover - trivial
        class R:
            def remote(self, *a, **k):
                return func(*a, **k)

        return R()

    def cluster_resources(self):  # pragma: no cover - trivial
        return {"CPU": 1}


@pytest.fixture
def dummy_ray(monkeypatch: pytest.MonkeyPatch):
    ray_mod = DummyRay()
    monkeypatch.setitem(sys.modules, "ray", ray_mod)
    monkeypatch.setattr(executors, "ray", ray_mod)
    return ray_mod


def test_ray_executor(monkeypatch: pytest.MonkeyPatch, dummy_ray) -> None:
    pids: list[int] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: DummyAgent(name, pids))
    monkeypatch.setattr(executors, "_execute_agent_remote", DummyRemote())
    monkeypatch.setattr(executors.search, "get_http_session", lambda: object())
    monkeypatch.setattr(executors.llm_pool, "get_session", lambda: object())
    cfg = ConfigModel(
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
