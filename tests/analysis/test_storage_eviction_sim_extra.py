"""Tests for storage eviction simulation."""

from tests.analysis.storage_eviction_sim_analysis import run


def test_storage_eviction_sim() -> None:
    results = run()
    assert results["normal"] == 0
    assert results["race"] == 0
    assert results["zero_budget"] == 9
    assert results["negative_budget"] == 9
    assert results["under_budget"] == 9
    assert results["no_nodes"] == 0
    assert results["exact_budget"] == 9
    assert results["burst"] == 0
    assert results["deterministic_override"] in {1, 2}
