# mypy: ignore-errors
"""Tests for scheduling_resource_benchmark script."""

from importlib import util
from pathlib import Path
import statistics

import pytest


def _load_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "scheduling_resource_benchmark.py"
    spec = util.spec_from_file_location("scheduling_resource_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scheduling_resource_benchmark module")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_benchmark_scaling():
    """More workers increase throughput and memory scales with tasks."""
    mod = _load_module()
    results = mod.run_benchmark(2, 3, 5, 20, 0.5)
    assert len(results) == 2

    one_worker, two_workers = results
    assert one_worker["expected_memory"] == 10.0
    assert len(one_worker["throughput_samples"]) == len(two_workers["throughput_samples"]) >= 3

    # Expect near-linear scaling: with twice the workers we target roughly twice the
    # throughput, but allow ±20% wiggle room for scheduling noise and benchmark
    # variability.
    assert two_workers["throughput"] == pytest.approx(
        one_worker["throughput"] * 2,
        rel=0.2,
    )

    # Require each sample to comfortably beat the corresponding single-worker
    # measurement. A 1.7x floor leaves room for momentary contention while still
    # flagging regressions that would erode the expected scaling benefit.
    paired_samples = list(
        zip(one_worker["throughput_samples"], two_workers["throughput_samples"])
    )
    assert all(two >= one * 1.7 for one, two in paired_samples)

    # The multi-worker samples should be both faster and stable: the slowest
    # multi-worker run must still outpace the fastest single-worker sample by a
    # healthy margin, and the multi-worker variability should stay tight.
    one_fastest = max(one_worker["throughput_samples"])
    two_slowest = min(two_workers["throughput_samples"])
    assert two_slowest >= one_fastest * 1.6

    multi_spread = max(two_workers["throughput_samples"]) / two_slowest
    assert multi_spread <= 1.15

    # The median per-sample speedup should stay aligned with the aggregate throughput.
    sample_speedups = [two / one for one, two in paired_samples]
    assert statistics.median(sample_speedups) == pytest.approx(2.0, rel=0.15)
