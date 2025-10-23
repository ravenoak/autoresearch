# mypy: ignore-errors
"""Unit tests for distributed executors with strict typing coverage."""

from __future__ import annotations

import importlib
import pickle
import types
from typing import Any, Callable, Dict, Iterable, List, Tuple, Type, Literal, cast

import pytest

from autoresearch.agents.base import Agent
from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.distributed.broker import (
    AgentResultMessage,
    BrokerMessage,
    InMemoryBroker,
    PersistClaimMessage,
    MessageQueueProtocol,
)
from autoresearch.distributed.executors import (
    ProcessExecutor,
    RayExecutor,
    _execute_agent_process,
    _execute_agent_remote,
    ray as ray_runtime,
)
from autoresearch.distributed.coordinator import publish_claim
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.reasoning_payloads import FrozenReasoningStep


class RecordingQueue(MessageQueueProtocol):
    """Test double that records broker interactions."""

    def __init__(self) -> None:
        self.items: List[BrokerMessage] = []

    def put(self, item: BrokerMessage) -> None:
        self.items.append(item)

    def get(self) -> BrokerMessage:
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
        assert msg["action"] == "agent_result"
        assert msg["agent"] == "Dummy"
        assert msg["result"]["results"]["final_answer"] == "done"
        assert msg["pid"] == queue.items[-1]["pid"]
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
            assert msg["action"] == "agent_result"
        recorded = queue.items[-1]
        assert recorded["agent"] == "Dummy"
        assert recorded["action"] == "agent_result"

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

            def __exit__(self, exc_type, exc, tb) -> Literal[False]:
                return False

            def starmap(
                self,
                func: Callable[..., AgentResultMessage],
                args: Iterable[Tuple[Any, ...]],
            ) -> List[AgentResultMessage]:
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
    """Ray transports QueryState instances without serialization failures.

    This is a regression guard for Ray serialization issues. Tests various
    QueryState configurations to ensure they can be serialized through Ray
    without errors, particularly focusing on the RLock serialization issue.
    """
    ray_module = pytest.importorskip("ray")
    ray_module.init(ignore_reinit_error=True, configure_logging=False)
    try:
        # Test basic QueryState
        basic_state = QueryState(query="test query")
        handle1 = ray_module.put(basic_state)
        restored1 = ray_module.get(handle1)
        assert isinstance(restored1, QueryState)
        assert restored1.query == "test query"
        assert hasattr(restored1, "_lock")  # Lock should be restored

        # Test complex QueryState with all fields populated
        complex_state = QueryState(query="complex query")
        complex_state.claims.append(FrozenReasoningStep({"id": "c1", "text": "test claim"}))
        complex_state.claim_audits = [{"id": "a1", "status": "verified"}]
        complex_state.sources = [{"id": "s1", "url": "http://example.com"}]
        complex_state.results = {"answer": "test result"}
        complex_state.messages = [{"from": "agent1", "content": "message"}]
        complex_state.feedback_events = [{"type": "feedback", "data": {}}]
        complex_state.coalitions = {"group1": ["agent1", "agent2"]}
        complex_state.metadata = {"test": {"nested": "value"}}
        complex_state.set_task_graph({"tasks": [{"id": "t1", "question": "Q"}], "edges": []})
        complex_state.react_log = [{"action": "test", "timestamp": 1234567890.0}]
        complex_state.react_traces = [{"trace": "test trace"}]
        complex_state.cycle = 5
        complex_state.primus_index = 2
        complex_state.last_updated = 1234567890.0
        complex_state.error_count = 1

        # This is the critical test - complex state through Ray
        handle2 = ray_module.put(complex_state)
        restored2 = ray_module.get(handle2)

        assert isinstance(restored2, QueryState)
        assert restored2.query == "complex query"
        assert len(restored2.claims) == 1
        assert restored2.claims[0]["id"] == "c1"
        assert isinstance(restored2.claims[0], FrozenReasoningStep)
        assert restored2.claim_audits == [{"id": "a1", "status": "verified"}]
        assert restored2.sources == [{"id": "s1", "url": "http://example.com"}]
        assert restored2.results == {"answer": "test result"}
        assert len(restored2.messages) == 1
        assert restored2.coalitions == {"group1": ["agent1", "agent2"]}
        # Check that metadata contains our test data (may also contain planner info)
        assert "test" in restored2.metadata
        assert restored2.metadata["test"] == {"nested": "value"}
        # Task graph should exist and have the expected structure (may be enhanced during processing)
        assert "tasks" in restored2.task_graph
        assert "edges" in restored2.task_graph
        assert len(restored2.task_graph["tasks"]) == 1
        assert restored2.task_graph["tasks"][0]["id"] == "t1"
        assert restored2.cycle == 5
        assert restored2.primus_index == 2
        assert restored2.error_count == 1
        assert hasattr(restored2, "_lock")  # Lock should be restored

        # Test pickle fallback (when Ray is not available)
        import pickle
        pickled = pickle.dumps(complex_state)
        restored_pickle = pickle.loads(pickled)
        assert isinstance(restored_pickle, QueryState)
        assert restored_pickle.query == "complex query"
        assert len(restored_pickle.claims) == 1
        assert restored_pickle.claims[0]["id"] == "c1"
        assert isinstance(restored_pickle.claims[0], FrozenReasoningStep)
        assert hasattr(restored_pickle, "_lock")  # Lock should be restored

    finally:
        ray_module.shutdown()


def test_publish_claim_enqueues_typed_message() -> None:
    broker = InMemoryBroker()
    try:
        claim = {"id": "c1", "text": "claim"}
        publish_claim(broker, claim, partial_update=True)
        message = broker.queue.get()
        assert message["action"] == "persist_claim"
        typed_message = cast(PersistClaimMessage, message)
        assert typed_message["claim"] == claim
        assert typed_message["partial_update"] is True
    finally:
        broker.shutdown()
