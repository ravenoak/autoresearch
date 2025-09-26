"""Tests for scheduling_resource_benchmark script."""

from importlib import util
from pathlib import Path

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

    # Expect near-linear scaling: with twice the workers we target roughly twice the
    # throughput, but allow ±20% wiggle room for scheduling noise and benchmark
    # variability.
    assert two_workers["throughput"] == pytest.approx(
        one_worker["throughput"] * 2,
        rel=0.2,
    )

    # Require each sample to comfortably beat the corresponding single-worker
    # measurement. A 1.5x floor gives headroom for momentary contention while still
    # flagging regressions that would erode the expected scaling benefit.
    paired_samples = zip(one_worker["throughput_samples"], two_workers["throughput_samples"])
    assert all(two >= one * 1.5 for one, two in paired_samples)
