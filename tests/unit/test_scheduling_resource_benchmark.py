"""Tests for scheduling_resource_benchmark script."""

from importlib import util
from pathlib import Path


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

    # The median throughput should scale noticeably once thread start-up costs
    # are amortized.
    assert two_workers["throughput"] >= one_worker["throughput"] * 1.2

    # Each individual throughput sample for two workers should comfortably
    # exceed the single-worker samples to guard against regressions in the
    # amortization logic. A small tolerance covers scheduler jitter.
    paired_samples = zip(one_worker["throughput_samples"], two_workers["throughput_samples"])
    assert all(two >= one * 1.1 for one, two in paired_samples)
