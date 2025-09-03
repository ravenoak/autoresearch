"""Validate scheduling benchmark simulation and resource usage."""

from tests.analysis.scheduling_resource_benchmark_analysis import run


def test_scheduling_benchmark_metrics() -> None:
    metrics = run()
    assert set(metrics) == {1, 2, 4}
    assert all(m["utilization"] < 1 for m in metrics.values())
    assert all(abs(m["expected_memory"] - 250.0) < 1e-6 for m in metrics.values())
    qlens = [metrics[w]["avg_queue_length"] for w in (1, 2, 4)]
    assert qlens[1] < qlens[0]
    assert qlens[2] <= qlens[1]
    thr = [metrics[w]["throughput"] for w in (1, 2, 4)]
    assert thr[1] > thr[0]
    assert thr[2] > thr[1]
    assert all(m["mem_kb"] >= 0 for m in metrics.values())
