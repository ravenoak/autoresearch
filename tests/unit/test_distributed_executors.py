"""Unit tests for distributed executors with strict typing coverage."""

from __future__ import annotations

import importlib
import pickle
import types
from typing import Any, Callable, Dict, Iterable, List, Tuple, Type

import pytest

from autoresearch.agents.base import Agent
from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.distributed.broker import MessageQueueProtocol
from autoresearch.distributed.executors import (
    ProcessExecutor,
    RayExecutor,
    _execute_agent_process,
    _execute_agent_remote,
    ray as ray_runtime,
)
from autoresearch.orchestration.state import QueryState


class RecordingQueue(MessageQueueProtocol):
    """Test double that records broker interactions."""

    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []

    def put(self, item: Dict[str, Any]) -> None:
        self.items.append(item)

    def get(self) -> Dict[str, Any]:
        return self.items.pop(0)

    def close(self) -> None:  # pragma: no cover - compatibility shim
        return None

    def join_thread(self) -> None:  # pragma: no cover - compatibility shim
        return None


class DummyAgent(Agent):
    name: str = "Dummy"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        return {"results": {"final_answer": "done"}}


class LocalFactory(AgentFactory):
    _registry: Dict[str, Type[Agent]] = {}
    _instances: Dict[str, Agent] = {}


def _register_dummy() -> None:
    AgentFactory.set_delegate(LocalFactory)
    AgentFactory.register("Dummy", DummyAgent)


def _unregister_dummy() -> None:
    AgentFactory.set_delegate(None)


def test_execute_agent_process_records_queue() -> None:
    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1)
        state = QueryState(query="q")
        queue = RecordingQueue()
        msg = _execute_agent_process("Dummy", state, config, result_queue=queue)
        assert msg["agent"] == "Dummy"
        assert msg["result"]["results"]["final_answer"] == "done"
        assert queue.items[-1] == msg
    finally:
        _unregister_dummy()


@pytest.mark.requires_distributed
def test_execute_agent_remote() -> None:
    """Remote execution follows docs/algorithms/distributed.md and coverage."""
    try:
        ray_module = importlib.import_module("ray")
    except Exception:
        ray_module = ray_runtime
    else:
        if not isinstance(ray_module, types.SimpleNamespace):
            pytest.skip(
                "Real Ray clusters require package-level agent registration;"
                " serialization is covered by test_query_state_ray_round_trip."
            )

    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1)
        state = QueryState(query="q")
        queue = RecordingQueue()
        msg_ref = _execute_agent_remote.remote("Dummy", state, config, result_queue=queue)
        # Reuse the stub runtime when Ray is unavailable.
        getter = getattr(ray_module, "get", None)
        if not callable(getter):
            getter = getattr(ray_runtime, "get", None)
        try:
            msg = getter(msg_ref) if callable(getter) else msg_ref
        except Exception as exc:  # pragma: no cover - surfaced in Ray regressions
            pytest.fail(f"ray.get failed for remote executor: {exc}")
        if isinstance(msg, dict):
            assert msg["agent"] == "Dummy"
            assert msg["result"]["results"]["final_answer"] == "done"
        assert queue.items[-1]["agent"] == "Dummy"

        enriched = QueryState(query="rich")
        enriched.claims.append({"id": "c1", "text": "claim"})
        enriched.metadata["planner"] = {"strategy": "map"}
        enriched.set_task_graph({"tasks": [{"id": "t1", "question": "Q"}], "edges": []})

        restored_state = pickle.loads(pickle.dumps(enriched))
        assert restored_state.claims == enriched.claims
        assert restored_state.metadata["planner"] == enriched.metadata["planner"]
        assert restored_state.task_graph == enriched.task_graph
    finally:
        _unregister_dummy()


@pytest.mark.requires_distributed
def test_ray_executor_cycle_callback() -> None:
    """RayExecutor invokes callbacks with typed state objects."""

    try:
        importlib.import_module("ray")
    except Exception:
        pass
    else:
        pytest.skip("RayExecutor callback test relies on the local stub runtime.")

    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1)
        executor = RayExecutor(config)
        calls: List[int] = []

        def on_cycle_end(loop: int, state: QueryState) -> None:
            assert isinstance(state, QueryState)
            calls.append(loop)

        response = executor.run_query("question", callbacks={"on_cycle_end": on_cycle_end})
        assert response.answer == "done"
        assert calls == [0]
    finally:
        executor.shutdown()
        _unregister_dummy()


def test_process_executor_uses_local_queue(monkeypatch) -> None:
    """ProcessExecutor reuses the message queue protocol implementation."""

    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1, distributed=False)

        class DummyPool:
            def __enter__(self) -> "DummyPool":
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

            def starmap(
                self,
                func: Callable[..., Dict[str, Any]],
                args: Iterable[Tuple[Any, ...]],
            ) -> List[Dict[str, Any]]:
                return [func(*call) for call in args]

        class DummyContext:
            def Pool(self, *args, **kwargs) -> DummyPool:  # pragma: no cover - simple shim
                return DummyPool()

        monkeypatch.setattr(
            "autoresearch.distributed.executors.multiprocessing.get_context",
            lambda *_args, **_kwargs: DummyContext(),
        )

        executor = ProcessExecutor(config)
        response = executor.run_query("question")
        assert response.answer == "done"
    finally:
        executor.shutdown()
        _unregister_dummy()


def test_query_state_cloudpickle_round_trip() -> None:
    """QueryState drops private locks during serialization and restores them."""
    cloudpickle = pytest.importorskip("cloudpickle")

    state = QueryState(query="q")
    state.add_message({"from": "tester", "content": "ping"})

    payload = cloudpickle.dumps(state)
    restored = cloudpickle.loads(payload)

    assert restored.messages[-1]["content"] == "ping"
    assert isinstance(getattr(restored, "_lock", None), type(state._lock))
    assert restored._lock is not state._lock

    restored.add_message({"from": "tester", "content": "pong"})
    assert restored.messages[-1]["content"] == "pong"


@pytest.mark.requires_distributed
def test_query_state_ray_round_trip() -> None:
    """Ray transports QueryState instances without serialization failures."""
    ray_module = pytest.importorskip("ray")
    ray_module.init(ignore_reinit_error=True, configure_logging=False)
    try:
        state = QueryState(query="q")
        handle = ray_module.put(state)
        restored = ray_module.get(handle)
        assert isinstance(restored, QueryState)
        assert restored.query == "q"
    finally:
        ray_module.shutdown()
