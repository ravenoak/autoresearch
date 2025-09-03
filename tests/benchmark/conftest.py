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
        data = json.loads(METRIC_BASELINE_FILE.read_text()) if METRIC_BASELINE_FILE.exists() else {}
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


TOKEN_MEMORY_FILE = Path(__file__).resolve().parents[1] / "data" / "token_memory_benchmark.json"


@pytest.fixture
def token_memory_baseline(
    request,
) -> Callable[[int, int, float, float, float], None]:
    """Record and compare token and resource metrics across runs."""

    def _check(
        in_tokens: int,
        out_tokens: int,
        memory_mb: float,
        duration: float,
        tolerance: float = 0.10,
    ) -> None:
        data = json.loads(TOKEN_MEMORY_FILE.read_text()) if TOKEN_MEMORY_FILE.exists() else {}
        key = request.node.nodeid
        baseline = data.get(key)
        if baseline is not None:
            assert in_tokens <= baseline["tokens"]["in"] * (1 + tolerance)
            assert out_tokens <= baseline["tokens"]["out"] * (1 + tolerance)
            assert memory_mb <= baseline["memory_delta_mb"] + tolerance
            assert duration <= baseline["duration_seconds"] * (1 + tolerance)
        data[key] = {
            "duration_seconds": duration,
            "memory_delta_mb": memory_mb,
            "tokens": {"in": in_tokens, "out": out_tokens},
        }
        TOKEN_MEMORY_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return _check
