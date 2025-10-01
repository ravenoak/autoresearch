from typing import cast

from scripts.api_stream_order_sim import _simulate


def test_api_stream_order_sim_invariants() -> None:
    """Streaming preserves order and emits heartbeats."""
    metrics = cast(dict[str, int | bool], _simulate(chunks=3))
    assert metrics["ordered"] is True
    assert metrics["heartbeats"] >= 3
    assert metrics["operations"] == 2 * 3 + 1
