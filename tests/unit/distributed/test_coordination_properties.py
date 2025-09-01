from __future__ import annotations

import random
import sys

sys.modules.setdefault("numpy", None)
from hypothesis import given, settings, strategies as st  # noqa: E402

from scripts.distributed_coordination_sim import (  # noqa: E402
    elect_leader,
    process_messages,
)


@given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, unique=True))
def test_election_converges_to_minimum(ids: list[int]) -> None:
    """Election converges to the global minimum identifier.

    See docs/algorithms/distributed_coordination.md for proof.
    """
    minimum = min(ids)
    for _ in range(3):
        shuffled = ids[:]
        random.shuffle(shuffled)
        assert elect_leader(shuffled) == minimum


@settings(deadline=None)
@given(st.lists(st.text(min_size=0, max_size=5), max_size=20))
def test_message_processing_is_idempotent(messages: list[str]) -> None:
    """Processing twice yields the same ordered sequence.

    See docs/algorithms/distributed_coordination.md for proof.
    """
    first = process_messages(messages)
    second = process_messages(first)
    assert first == second == messages
