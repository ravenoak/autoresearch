"""Regression tests for :mod:`autoresearch.orchestration.state`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.state_registry import QueryStateRegistry


@pytest.fixture(autouse=True)
def _clear_registry() -> Iterator[None]:
    """Ensure registry state isolation across tests."""

    QueryStateRegistry._store.clear()
    try:
        yield
    finally:
        QueryStateRegistry._store.clear()


def test_query_state_cloudpickle_serialization_preserves_fields() -> None:
    """`cloudpickle` round-trips retain planner metadata and claims."""

    cloudpickle = pytest.importorskip("cloudpickle")

    state = QueryState(query="serial")
    state.claims.append({"id": "c1", "text": "claim"})
    state.metadata["planner"] = {"strategy": "map"}
    state.set_task_graph(
        {
            "objectives": ["Persist graph"],
            "tasks": [
                {
                    "id": "t1",
                    "question": "Q",
                    "tool_affinity": {"search": 0.4},
                    "exit_criteria": ["complete"],
                    "explanation": "baseline",
                }
            ],
            "edges": [],
        }
    )

    payload = cloudpickle.dumps(state)
    restored = cloudpickle.loads(payload)

    assert restored.claims == state.claims
    assert restored.metadata["planner"] == state.metadata["planner"]
    assert restored.task_graph == state.task_graph
    assert restored.metadata["planner"]["telemetry"] == state.metadata["planner"]["telemetry"]


def test_query_state_registry_clone_produces_independent_copies() -> None:
    """Cloned states remain independent and retain functioning locks."""

    state = QueryState(query="registry-clone")
    state.metadata["counter"] = 1
    config = ConfigModel()

    state_id = QueryStateRegistry.register(state, config)
    state.metadata["counter"] = 99

    clone_result = QueryStateRegistry.clone(state_id)
    assert clone_result is not None
    cloned_state, cloned_config = clone_result
    assert cloned_state.metadata["counter"] == 1
    assert cloned_config.backend == config.backend

    assert cloned_state._lock.acquire(blocking=False)
    cloned_state._lock.release()

    cloned_state.metadata["counter"] = 2
    cloned_config.backend = "updated-backend"

    second_result = QueryStateRegistry.clone(state_id)
    assert second_result is not None
    second_state, second_config = second_result
    assert second_state is not cloned_state
    assert second_state.metadata["counter"] == 1
    assert second_config.backend == config.backend
    assert second_state._lock.acquire(blocking=False)
    second_state._lock.release()


def test_query_state_model_copy_deep_clone_separates_mutable_data() -> None:
    """`model_copy(deep=True)` keeps locks healthy and nested data independent."""

    state = QueryState(query="memoized-locks")
    state.metadata["nested"] = {"inner": {"value": 1}}

    state_id = QueryStateRegistry.register(state, ConfigModel())
    stored_state = QueryStateRegistry._store[state_id].state

    clone = stored_state.model_copy(deep=True)

    clone.metadata["nested"]["inner"]["value"] = 5

    assert stored_state.metadata["nested"]["inner"]["value"] == 1
    assert clone.metadata["nested"]["inner"]["value"] == 5
    assert clone._lock is not stored_state._lock
    assert isinstance(clone._lock, type(stored_state._lock))


def test_query_state_registry_update_refreshes_snapshots() -> None:
    """Updates replace stored snapshots with fresh copies and locks."""

    initial_state = QueryState(query="initial")
    initial_state.metadata["value"] = "original"
    state_id = QueryStateRegistry.register(initial_state, ConfigModel())

    updated_state = QueryState(query="updated")
    updated_state.metadata["value"] = "replaced"
    new_config = ConfigModel(gate_policy_enabled=False)

    QueryStateRegistry.update(state_id, updated_state, new_config)

    snapshot = QueryStateRegistry.get_snapshot(state_id)
    assert snapshot is not None
    assert snapshot.state.metadata["value"] == "replaced"
    assert snapshot.config.gate_policy_enabled is False

    clone_result = QueryStateRegistry.clone(state_id)
    assert clone_result is not None
    cloned_state, cloned_config = clone_result
    assert cloned_state.query == "updated"
    assert cloned_config.gate_policy_enabled is False
    assert cloned_state._lock.acquire(blocking=False)
    cloned_state._lock.release()
