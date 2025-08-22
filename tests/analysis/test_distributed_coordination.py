from tests.analysis.distributed_coordination_analysis import run


def test_distributed_coordination_metrics() -> None:
    metrics = run()
    assert set(metrics) == {1, 2, 4}
    assert all(m["memory_mb"] > 0 for m in metrics.values())
