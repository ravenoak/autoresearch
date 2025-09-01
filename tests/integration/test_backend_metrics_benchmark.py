"""Benchmark precision, recall, and latency across search backends."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import pytest

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "backend_benchmark.csv"


def load_data() -> List[Dict[str, str]]:
    """Load benchmark rows from the shared dataset."""
    with DATA_PATH.open() as f:
        return list(csv.DictReader(f))


def compute_metrics(rows: List[Dict[str, str]]) -> tuple[float, float]:
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


pytestmark = [pytest.mark.slow, pytest.mark.integration]
pytest.importorskip("pytest_benchmark")


def test_backend_metrics(benchmark, metrics_baseline) -> None:
    """Record metrics for each backend and check against baselines."""
    rows = load_data()
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["backend"], []).append(row)
    for backend, data in grouped.items():
        def run() -> None:
            for _ in range(1000):
                compute_metrics(data)

        latency = benchmark(run)
        precision, recall = compute_metrics(data)
        metrics_baseline(backend, precision, recall, latency)
