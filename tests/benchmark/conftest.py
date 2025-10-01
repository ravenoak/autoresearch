"""Shared fixtures for benchmark tests."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import pytest

METRIC_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "backend_metrics.json"


class MetricsBaselineFn(Protocol):
    """Callable signature for backend metric comparisons."""

    def __call__(
        self,
        backend: str,
        precision: float,
        recall: float,
        latency: float,
        tolerance: float = ...,
    ) -> None:
        ...


@pytest.fixture
def metrics_baseline(
    request: pytest.FixtureRequest,
) -> Iterator[MetricsBaselineFn]:
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

    yield _check


TOKEN_MEMORY_FILE = Path(__file__).resolve().parents[1] / "data" / "token_memory_benchmark.json"


class TokenMemoryBaselineFn(Protocol):
    """Callable signature for token and memory baseline comparisons."""

    def __call__(
        self,
        in_tokens: int,
        out_tokens: int,
        memory_mb: float,
        duration: float,
        tolerance: float = ...,
    ) -> None:
        ...


@pytest.fixture
def token_memory_baseline(
    request: pytest.FixtureRequest,
) -> Iterator[TokenMemoryBaselineFn]:
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

    yield _check
