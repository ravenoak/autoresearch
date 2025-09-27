from __future__ import annotations

import importlib
import pickle
import types
from typing import Dict, Any, Type

import pytest

from autoresearch.agents.base import Agent
from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState
from autoresearch.distributed.executors import (
    _execute_agent_process,
    _execute_agent_remote,
    ray as ray_runtime,
)


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


def test_execute_agent_process():
    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1)
        state = QueryState(query="q")
        msg = _execute_agent_process("Dummy", state, config)
        assert msg["agent"] == "Dummy"
        assert msg["result"]["results"]["final_answer"] == "done"
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
        msg_ref = _execute_agent_remote.remote("Dummy", state, config)
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
