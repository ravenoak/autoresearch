"""Unit tests for :mod:`autoresearch.orchestration.state_registry`."""

from __future__ import annotations

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import LOCK_TYPE, QueryState
from autoresearch.orchestration.state_registry import QueryStateRegistry


@pytest.fixture(autouse=True)
def clear_state_registry() -> None:
    """Reset the in-memory registry before and after each test."""

    QueryStateRegistry._store.clear()
    yield
    QueryStateRegistry._store.clear()


def test_register_and_clone_preserve_lock_and_metadata_types() -> None:
    """Registered snapshots keep metadata typing and recreate locks on clone."""

    state = QueryState(
        query="dialectical reasoning",
        metadata={"score": 0.75, "flags": {"high_priority": True}},
    )
    config = ConfigModel(loops=3, tracing_enabled=True)

    state_id = QueryStateRegistry.register(state, config)

    cloned = QueryStateRegistry.clone(state_id)
    assert cloned is not None
    cloned_state, cloned_config = cloned

    assert cloned_state is not state
    assert cloned_config is not config
    assert isinstance(cloned_state._lock, LOCK_TYPE)
    assert cloned_state._lock is not state._lock
    assert isinstance(cloned_state.metadata["score"], float)
    assert isinstance(cloned_state.metadata["flags"], dict)
    assert isinstance(cloned_state.metadata["flags"]["high_priority"], bool)


def test_update_replaces_snapshot_and_preserves_lock_integrity() -> None:
    """Updating an existing entry refreshes the snapshot while keeping typing."""

    base_state = QueryState(query="initial")
    base_state.metadata["score"] = 0.5
    state_id = QueryStateRegistry.register(base_state, ConfigModel(loops=2))

    new_state = QueryState(
        query="updated",
        metadata={"score": 2.5, "flags": {"high_priority": False}},
    )
    new_state.metadata["extra"] = {"attempts": 1}
    new_config = ConfigModel(loops=7, tracing_enabled=False)

    QueryStateRegistry.update(state_id, new_state, config=new_config)

    cloned = QueryStateRegistry.clone(state_id)
    assert cloned is not None
    updated_state, updated_config = cloned

    assert updated_state.query == "updated"
    assert updated_config.loops == 7
    assert updated_config is not new_config
    assert isinstance(updated_state._lock, LOCK_TYPE)
    assert updated_state._lock is not new_state._lock
    assert updated_state.metadata is not new_state.metadata
    assert isinstance(updated_state.metadata["score"], float)
    assert isinstance(updated_state.metadata["flags"], dict)
    assert isinstance(updated_state.metadata["flags"]["high_priority"], bool)
    assert isinstance(updated_state.metadata["extra"], dict)


def test_update_creates_snapshot_when_missing_identifier() -> None:
    """Missing identifiers create new snapshots with default config typing."""

    missing_state = QueryState(
        query="late-registered",
        metadata={"score": 1, "flags": {"high_priority": True}},
    )
    missing_state.metadata["attempts"] = 3
    missing_id = "missing-id"

    QueryStateRegistry.update(missing_id, missing_state)

    cloned = QueryStateRegistry.clone(missing_id)
    assert cloned is not None
    inserted_state, inserted_config = cloned

    assert inserted_state.query == "late-registered"
    assert isinstance(inserted_state._lock, LOCK_TYPE)
    assert inserted_state._lock is not missing_state._lock
    assert inserted_state.metadata is not missing_state.metadata
    assert isinstance(inserted_state.metadata["score"], int)
    assert isinstance(inserted_state.metadata["flags"], dict)
    assert isinstance(inserted_state.metadata["flags"]["high_priority"], bool)
    assert isinstance(inserted_state.metadata["attempts"], int)
    assert inserted_config.loops == ConfigModel().loops
