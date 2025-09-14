import contextlib
import os

import pytest

from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch.distributed import executors, ProcessExecutor
from multiprocessing import resource_tracker
from types import SimpleNamespace
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState


def _dummy_execute_agent_process(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    result_queue=None,
    storage_queue=None,
):
    msg = {
        "action": "agent_result",
        "agent": agent_name,
        "result": {"results": {agent_name: "ok"}},
        "pid": os.getpid(),
    }
    if result_queue is not None:
        result_queue.put(msg)
    return msg


@pytest.fixture
def process_executor(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> ProcessExecutor:
    """Provide a ProcessExecutor that shuts down cleanly after the test."""

    monkeypatch.setattr(executors, "_execute_agent_process", _dummy_execute_agent_process)

    class DummyPool:
        def __init__(self) -> None:
            self.closed = False
            self.joined = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.close()
            self.join()
            return False

        def close(self) -> None:
            self.closed = True

        def join(self) -> None:
            self.joined = True

        def starmap(self, func, args):
            return [func(*a) for a in args]

    pool = DummyPool()
    monkeypatch.setattr(
        executors.multiprocessing,
        "get_context",
        lambda _: SimpleNamespace(Pool=lambda processes=None: pool),
    )
    cfg = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=False,
        distributed_config=DistributedConfig(enabled=False, num_cpus=2),
    )
    executor = ProcessExecutor(cfg)

    def _cleanup() -> None:
        executor.shutdown()
        with contextlib.suppress(Exception):
            cache = resource_tracker._resource_tracker._cache.copy()
            for name, rtype in cache.items():
                resource_tracker.unregister(name, rtype)
                resource_tracker._resource_tracker.maybe_unlink(name, rtype)
        assert pool.closed and pool.joined

    request.addfinalizer(_cleanup)
    return executor


@pytest.mark.integration
def test_process_executor_runs(process_executor: ProcessExecutor):
    """Ensure distributed queries complete without hanging."""

    resp = process_executor.run_query("q")
    assert isinstance(resp, QueryResponse)
