"""Validate message throughput scaling for the distributed simulation."""

from tests.analysis.distributed_sim_analysis import run
from scripts import distributed_orchestrator_sim


def test_message_throughput_scales() -> None:
    metrics = run()
    assert set(metrics) == {1, 2, 4}
    throughputs = [metrics[w]["throughput"] for w in (1, 2, 4)]
    assert throughputs[1] >= throughputs[0] * 0.75
    assert throughputs[2] >= throughputs[1] * 0.75
    assert all(m["memory_mb"] > 0 for m in metrics.values())


def test_scheduling_latency_scales() -> None:
    metrics = {
        w: [
            distributed_orchestrator_sim.run_simulation(
                workers=w, tasks=20, network_latency=0.001
            )
            for _ in range(3)
        ]
        for w in (1, 2, 4)
    }
    latencies = [
        sum(sample["avg_latency_s"] for sample in metrics[w]) / len(metrics[w])
        for w in (1, 2, 4)
    ]
    assert latencies[1] <= latencies[0] * 1.05
    assert latencies[2] <= latencies[1] * 1.05
    assert all(run["memory_mb"] > 0 for runs in metrics.values() for run in runs)
