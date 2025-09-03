"""Validate output and scaling for the distributed orchestrator benchmark."""

from tests.analysis.distributed_orchestrator_perf_benchmark_analysis import run


def test_benchmark_output_and_scaling() -> None:
    metrics = run()
    assert set(metrics) == {1, 2, 4}
    for data in metrics.values():
        assert {"avg_latency_s", "throughput", "memory_mb"} <= data.keys()
        assert data["memory_mb"] > 0
    lats = [metrics[w]["avg_latency_s"] for w in (1, 2, 4)]
    thr = [metrics[w]["throughput"] for w in (1, 2, 4)]
    assert lats[1] < lats[0]
    assert lats[2] < lats[0]
    assert thr[1] > thr[0]
    assert thr[2] > 0
