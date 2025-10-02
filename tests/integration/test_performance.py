"""Performance benchmarks for query execution."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Callable, Mapping

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

pytestmark = pytest.mark.slow

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_token_memory.py"
spec = importlib.util.spec_from_file_location("benchmark_token_memory", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load benchmark_token_memory module")
benchmark_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark_module)
run_benchmark: Callable[[], Mapping[str, object]] = benchmark_module.run_benchmark

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_memory.json"


def test_query_time_and_memory(
    benchmark: BenchmarkFixture,
    token_baseline: Callable[[dict[str, dict[str, int]], int], None],
) -> None:
    """Queries should stay within expected time and memory bounds."""

    metrics: Mapping[str, object] = benchmark(run_benchmark)
    baseline: Mapping[str, object] = json.loads(BASELINE_PATH.read_text())

    assert metrics["tokens"] == baseline["tokens"]
    assert metrics["memory_delta_mb"] <= baseline["memory_delta_mb"] + 5
    assert metrics["duration_seconds"] <= baseline["duration_seconds"] * 2

    token_baseline(metrics["tokens"])
