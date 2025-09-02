"""Shared fixtures for benchmark tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

METRIC_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "backend_metrics.json"


@pytest.fixture
def metrics_baseline(request) -> Callable[[str, float, float, float], None]:
    """Record and compare backend metrics across test runs."""

    def _check(
        backend: str,
        precision: float,
        recall: float,
        latency: float,
        tolerance: float = 0.05,
    ) -> None:
        data = (
            json.loads(METRIC_BASELINE_FILE.read_text())
            if METRIC_BASELINE_FILE.exists()
            else {}
        )
        key = f"{request.node.nodeid}::{backend}"
        baseline = data.get(key)
        if baseline is not None:
            assert precision >= baseline["precision"] - tolerance
            assert recall >= baseline["recall"] - tolerance
            assert latency <= baseline["latency"] * (1 + tolerance)
        data[key] = {
            "precision": precision,
            "recall": recall,
            "latency": latency,
        }
        METRIC_BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return _check
