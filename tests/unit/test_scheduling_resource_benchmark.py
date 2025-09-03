"""Tests for scheduling_resource_benchmark script."""

from importlib import util
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "scheduling_resource_benchmark.py"
    spec = util.spec_from_file_location("scheduling_resource_benchmark", path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_benchmark_scaling():
    """More workers increase throughput and memory scales with tasks."""
    mod = load_module()
    results = mod.run_benchmark(2, 3, 5, 20, 0.5)
    assert len(results) == 2
    assert results[1]["throughput"] > results[0]["throughput"]
    assert results[0]["expected_memory"] == 10.0
