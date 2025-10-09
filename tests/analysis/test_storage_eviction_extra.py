"""Tests for storage eviction simulations."""

from tests.analysis.storage_eviction_analysis import run


def test_storage_eviction() -> None:
    evicted = run()
    assert evicted["LRU"] == ["b"]
    assert evicted["FIFO"] == ["a"]
