"""Shared fixtures for benchmark tests."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from typing import TypedDict, cast

METRIC_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "backend_metrics.json"


class BackendMetricsRecord(TypedDict):
    """Serialized backend metrics tracked across runs."""

    precision: float
    recall: float
    latency: float


BackendMetricsStore = dict[str, BackendMetricsRecord]


MetricsBaselineFn = Callable[[str, float, float, float], None]


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
        *,
        tolerance: float = 0.05,
    ) -> None:
        data: BackendMetricsStore
        if METRIC_BASELINE_FILE.exists():
            raw = json.loads(METRIC_BASELINE_FILE.read_text())
            data = cast(BackendMetricsStore, raw)
        else:
            data = {}
        key = f"{request.node.nodeid}::{backend}"
        baseline = data.get(key)
        if baseline is not None:
            assert precision >= baseline["precision"] - tolerance
            assert recall >= baseline["recall"] - tolerance
            assert latency <= baseline["latency"] * (1 + tolerance)
        record: BackendMetricsRecord = {
            "precision": precision,
            "recall": recall,
            "latency": latency,
        }
        data[key] = record
        METRIC_BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    yield _check


TOKEN_MEMORY_FILE = Path(__file__).resolve().parents[1] / "data" / "token_memory_benchmark.json"


TokenCounts = TypedDict("TokenCounts", {"in": int, "out": int})


class TokenMemoryRecord(TypedDict):
    """Serialized token and memory metrics tracked across runs."""

    duration_seconds: float
    memory_delta_mb: float
    tokens: TokenCounts


TokenMemoryStore = dict[str, TokenMemoryRecord]


TokenMemoryBaselineFn = Callable[[int, int, float, float], None]


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
        *,
        tolerance: float = 0.10,
    ) -> None:
        data: TokenMemoryStore
        if TOKEN_MEMORY_FILE.exists():
            raw = json.loads(TOKEN_MEMORY_FILE.read_text())
            data = cast(TokenMemoryStore, raw)
        else:
            data = {}
        key = request.node.nodeid
        baseline = data.get(key)
        if baseline is not None:
            assert in_tokens <= baseline["tokens"]["in"] * (1 + tolerance)
            assert out_tokens <= baseline["tokens"]["out"] * (1 + tolerance)
            assert memory_mb <= baseline["memory_delta_mb"] + tolerance
            assert duration <= baseline["duration_seconds"] * (1 + tolerance)
        record: TokenMemoryRecord = {
            "duration_seconds": duration,
            "memory_delta_mb": memory_mb,
            "tokens": {"in": in_tokens, "out": out_tokens},
        }
        data[key] = record
        TOKEN_MEMORY_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    yield _check
