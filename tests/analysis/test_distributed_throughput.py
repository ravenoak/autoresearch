"""Validate throughput scaling for the distributed simulation."""

from tests.analysis.distributed_throughput_analysis import run


def test_throughput_scales_with_workers() -> None:
    metrics = run()
    assert set(metrics) == {1, 2, 4}
    throughputs = [metrics[w]["throughput"] for w in (1, 2, 4)]
    assert throughputs[1] > throughputs[0]
    assert throughputs[2] > throughputs[1]
    assert all(m["memory_mb"] > 0 for m in metrics.values())
