"""Benchmark relevance ranking convergence."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ranking_convergence.py"
_spec = importlib.util.spec_from_file_location("ranking_convergence", SCRIPT)
module = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(module)

pytestmark = [pytest.mark.slow]


def test_ranking_convergence_simulation(benchmark, metrics_baseline) -> None:
    """Mean convergence step remains one across random runs."""

    def run() -> None:
        module.run_trials(trials=100, items=5)

    benchmark(run)
    mean = module.run_trials(trials=100, items=5)
    assert mean == pytest.approx(1.0)
    latency = benchmark.stats["mean"]
    metrics_baseline("ranking_convergence", mean, mean, latency)
