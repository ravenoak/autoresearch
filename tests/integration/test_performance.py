"""Performance benchmarks for query execution."""

import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_token_memory.py"
spec = importlib.util.spec_from_file_location("benchmark_token_memory", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load benchmark_token_memory module")
benchmark_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark_module)
run_benchmark = benchmark_module.run_benchmark

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_memory.json"


def test_query_time_and_memory(benchmark, token_baseline):
    """Queries should stay within expected time and memory bounds."""

    metrics = benchmark(run_benchmark)
    baseline = json.loads(BASELINE_PATH.read_text())

    assert metrics["tokens"] == baseline["tokens"]
    assert metrics["memory_delta_mb"] <= baseline["memory_delta_mb"] + 5
    assert metrics["duration_seconds"] <= baseline["duration_seconds"] * 2

    token_baseline(metrics["tokens"])
