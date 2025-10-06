"""Unit tests for helpers in `orchestration.metrics`."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from types import SimpleNamespace

from autoresearch.orchestration import metrics


def test_mean_last_nonzero() -> None:
    values = [0, 5, 0, 10, 0]
    assert metrics._mean_last_nonzero(values, n=2) == 7.5


def test_temporary_metrics_restores_state(tmp_path: Path) -> None:
    # Provide histogram with internal counters required by reset_metrics
    metrics.KUZU_QUERY_TIME = cast(
        Any,
        SimpleNamespace(
            _sum=SimpleNamespace(set=lambda x: None, get=lambda: 0.0),
            _count=SimpleNamespace(set=lambda x: None, get=lambda: 0.0),
        ),
    )
    metrics.reset_metrics()
    metrics.QUERY_COUNTER.inc()
    before = metrics.QUERY_COUNTER._value.get()
    with metrics.temporary_metrics():
        metrics.QUERY_COUNTER.inc(5)
    after = metrics.QUERY_COUNTER._value.get()
    assert before == after


def test_record_query_and_tokens(tmp_path: Path) -> None:
    metrics.reset_metrics()
    metrics.record_query()
    assert metrics.QUERY_COUNTER._value.get() == 1
    m = metrics.OrchestrationMetrics()
    m.record_tokens("A", 2, 3)
    file = tmp_path / "tokens.json"
    m.record_query_tokens("q", file)
    assert "q" in file.read_text()
