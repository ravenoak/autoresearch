from __future__ import annotations

import random
import sys
import multiprocessing
from pathlib import Path

import pytest

sys.modules.setdefault("numpy", None)  # type: ignore[arg-type]
from hypothesis import HealthCheck, given, settings, strategies as st  # noqa: E402

from scripts.distributed_coordination_sim import (  # noqa: E402
    elect_leader,
    process_messages,
)


@pytest.fixture(scope="session", autouse=True)
def set_spawn_start_method() -> None:
    """Use spawn to avoid fork-related deadlocks in multiprocessing."""
    multiprocessing.set_start_method("spawn", force=True)


@pytest.fixture
def tmp_path_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ensure multiprocessing uses the per-test temp directory."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    return tmp_path


@settings(
    max_examples=10,
    deadline=1000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=20,
        unique=True,
    )
)
def test_election_converges_to_minimum(tmp_path_env: Path, ids: list[int]) -> None:
    """Election converges to the global minimum identifier.

    See docs/algorithms/distributed_coordination.md for proof.
    """
    minimum = min(ids)
    for _ in range(3):
        shuffled = ids[:]
        random.shuffle(shuffled)
        assert elect_leader(shuffled) == minimum


# The processing pipeline can run longer on constrained runners. Limit the
# workload and apply a generous Hypothesis deadline to prevent hangs during
# coverage runs.
@settings(
    max_examples=3,
    deadline=None,  # Disable deadline to avoid hypothesis timeouts during coverage
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(st.lists(st.text(min_size=0, max_size=5), max_size=5))
def test_message_processing_is_idempotent(tmp_path_env: Path, messages: list[str]) -> None:
    """Processing twice yields the same ordered sequence.

    See docs/algorithms/distributed_coordination.md for proof.
    """
    first = process_messages(messages)
    second = process_messages(first)
    assert first == second == messages
