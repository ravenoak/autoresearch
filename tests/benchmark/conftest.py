"""Shared fixtures for benchmark tests."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TypedDict

import pytest

METRIC_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "backend_metrics.json"


class BackendMetricsRecord(TypedDict):
    """Serialized backend metrics tracked across runs."""

    precision: float
    recall: float
    latency: float


BackendMetricsStore = dict[str, BackendMetricsRecord]


def _load_backend_metrics(path: Path) -> BackendMetricsStore:
    """Load backend metrics from ``path`` enforcing the expected schema."""

    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):  # pragma: no cover - defensive programming
        raise TypeError("backend metrics file must contain a mapping")
    metrics: BackendMetricsStore = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise TypeError("backend metrics values must be objects")
        precision = float(value["precision"])
        recall = float(value["recall"])
        latency = float(value["latency"])
        metrics[str(key)] = BackendMetricsRecord(
            precision=precision,
            recall=recall,
            latency=latency,
        )
    return metrics


def _persist_backend_metrics(path: Path, data: BackendMetricsStore) -> None:
    """Persist ``data`` to ``path`` using canonical formatting."""

    path.write_text(json.dumps(data, indent=2, sort_keys=True))


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
        data = _load_backend_metrics(METRIC_BASELINE_FILE)
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
        _persist_backend_metrics(METRIC_BASELINE_FILE, data)

    yield _check


TOKEN_MEMORY_FILE = Path(__file__).resolve().parents[1] / "data" / "token_memory_benchmark.json"


TokenCounts = TypedDict("TokenCounts", {"in": int, "out": int})


class TokenMemoryRecord(TypedDict):
    """Serialized token and memory metrics tracked across runs."""

    duration_seconds: float
    memory_delta_mb: float
    tokens: TokenCounts


TokenMemoryStore = dict[str, TokenMemoryRecord]


def _load_token_memory(path: Path) -> TokenMemoryStore:
    """Load token memory metrics enforcing the expected schema."""

    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):  # pragma: no cover - defensive programming
        raise TypeError("token memory file must contain a mapping")
    metrics: TokenMemoryStore = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise TypeError("token memory values must be objects")
        tokens_value = value["tokens"]
        if not isinstance(tokens_value, dict):
            raise TypeError("token counts must be objects")
        tokens: TokenCounts = {
            "in": int(tokens_value["in"]),
            "out": int(tokens_value["out"]),
        }
        metrics[str(key)] = TokenMemoryRecord(
            duration_seconds=float(value["duration_seconds"]),
            memory_delta_mb=float(value["memory_delta_mb"]),
            tokens=tokens,
        )
    return metrics


def _persist_token_memory(path: Path, data: TokenMemoryStore) -> None:
    """Persist token memory data using canonical formatting."""

    path.write_text(json.dumps(data, indent=2, sort_keys=True))


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
        data = _load_token_memory(TOKEN_MEMORY_FILE)
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
        _persist_token_memory(TOKEN_MEMORY_FILE, data)

    yield _check
