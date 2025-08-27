from __future__ import annotations

import sys

sys.modules.setdefault("numpy", None)
from hypothesis import given, strategies as st  # noqa: E402

from scripts.distributed_coordination_sim import elect_leader, process_messages  # noqa: E402


@given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, unique=True))
def test_leader_is_minimum(ids: list[int]) -> None:
    """Leader election chooses the smallest identifier."""
    leader = elect_leader(ids)
    assert leader in ids
    assert leader == min(ids)


@given(st.lists(st.text(min_size=0, max_size=5), max_size=20))
def test_message_ordering_preserved(messages: list[str]) -> None:
    """Broker delivers messages in the order they were sent."""
    delivered = process_messages(messages)
    assert delivered == messages
