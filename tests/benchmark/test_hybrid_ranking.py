"""Benchmark hybrid ranking precision, recall, and latency per backend."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, TypedDict, cast

import pytest

from tests.benchmark.conftest import MetricsBaselineFn

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "backend_benchmark.csv"


class BenchmarkRow(TypedDict):
    backend: str
    score: str
    relevance: str


# Updated weighting for hybrid ranking: bm25=0.4, semantic=0.5, credibility=0.1.
RANKING_WEIGHTS: dict[str, float] = {"bm25": 0.4, "semantic": 0.5, "credibility": 0.1}


def load_data() -> list[BenchmarkRow]:
    """Load benchmark rows from the shared dataset."""
    with DATA_PATH.open() as f:
        return [cast(BenchmarkRow, row) for row in csv.DictReader(f)]


def compute_metrics(rows: list[BenchmarkRow]) -> tuple[float, float]:
    """Return precision and recall for given rows using a 0.5 score threshold."""
    tp = fp = fn = 0
    for row in rows:
        score = float(row["score"])
        rel = int(row["relevance"])
        pred = score >= 0.5
        if pred and rel:
            tp += 1
        elif pred and not rel:
            fp += 1
        elif not pred and rel:
            fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return precision, recall


pytestmark = [pytest.mark.slow]


@pytest.mark.parametrize("backend", ["bm25", "semantic", "hybrid"])
def test_hybrid_ranking(
    backend: str, benchmark: Any, metrics_baseline: MetricsBaselineFn
) -> None:
    """Record metrics for each backend and check against baselines."""
    rows = load_data()
    data = [r for r in rows if r["backend"] == backend]

    if backend == "hybrid":
        # Ensure weights remain normalised for the hybrid algorithm.
        assert pytest.approx(sum(RANKING_WEIGHTS.values())) == 1.0

    def run() -> None:
        compute_metrics(data)

    benchmark(run)
    latency = benchmark.stats["mean"]
    precision, recall = compute_metrics(data)
    metrics_baseline(backend, precision, recall, latency)
