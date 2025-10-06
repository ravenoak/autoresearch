"""Tests for distributed coordination benchmark."""

import pytest

from scripts.distributed_coordination_benchmark import benchmark

pytestmark = [pytest.mark.requires_distributed]


@pytest.mark.skip(reason="multiprocessing Manager unsupported in this environment")
def test_benchmark_scales() -> None:
    """Throughput increases with additional workers."""

    one = benchmark(1, 2)
    two = benchmark(2, 2)
    assert two["throughput"] > one["throughput"] > 0


@pytest.mark.skip(reason="multiprocessing Manager unsupported in this environment")
def test_benchmark_survives_worker_crash() -> None:
    """Benchmark processes messages even when a worker crashes."""

    metrics = benchmark(2, 2, fail=True)
    assert metrics["messages"] >= 2
    assert metrics["messages"] < 4
    assert metrics["throughput"] > 0
