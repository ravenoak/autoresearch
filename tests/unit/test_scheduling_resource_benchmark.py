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
    assert results[1]["throughput"] > results[0]["throughput"]
    assert results[0]["expected_memory"] == 10.0
