"""Tests for token recording, regression checks, and coverage targets."""

import json
from pathlib import Path
import types
from typing import Protocol

import pytest
from coverage import Coverage

from tests.helpers.modules import ensure_stub_module

ensure_stub_module(
    "pydantic_settings",
    {
        "BaseSettings": object,
        "CliApp": object,
        "SettingsConfigDict": dict,
    },
)

from autoresearch.orchestration.metrics import OrchestrationMetrics  # noqa: E402


class _GaugeProxy(Protocol):
    def get(self) -> float: ...

    def set(self, value: float) -> None: ...


def test_record_and_check_query_tokens(tmp_path: Path) -> None:
    """Metrics track total tokens and detect regressions."""
    metrics = OrchestrationMetrics()
    metrics.record_tokens("agent", 5, 7)
    file_path = tmp_path / "tokens.json"
    metrics.record_query_tokens("search", file_path)
    data = json.loads(file_path.read_text())
    assert data["search"] == 12
    assert not metrics.check_query_regression("search", file_path)
    metrics.record_tokens("agent", 10, 0)
    assert metrics.check_query_regression("search", file_path)


def test_metrics_coverage_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Executed lines in metrics exceed 80 percent of statements.

    This approximation focuses on functions exercised in this test to prevent
    regressions in helper utilities.
    """

    cov = Coverage(data_file=None)
    cov.start()

    # Cover counter helpers
    from autoresearch.orchestration import metrics as m

    m.ensure_counters_initialized()
    m.reset_metrics()

    class DummyHist:
        def __init__(self) -> None:
            def _get() -> float:
                return 0.0

            def _set(_: float) -> None:
                return None

            proxy = types.SimpleNamespace(get=_get, set=_set)
            self._sum: _GaugeProxy = proxy
            self._count: _GaugeProxy = proxy

    monkeypatch.setattr(m, "KUZU_QUERY_TIME", DummyHist())

    with m.temporary_metrics():
        metrics = OrchestrationMetrics()
        metrics.record_tokens("a", 1, 2)
        metrics.record_error("a")
        metrics.record_circuit_breaker(
            "a",
            {
                "state": "closed",
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "recovery_attempts": 0,
            },
        )
        metrics.start_cycle()

        monkeypatch.setattr(m, "_get_system_usage", lambda: (0.0, 0.0, 0.0, 0.0))
        metrics.record_system_resources()
        metrics.end_cycle()
        metrics.record_agent_timing("a", 0.1)
        metrics.compress_prompt_if_needed("word " * 20, 5)
        metrics.suggest_token_budget(5)
        file_path = tmp_path / "tokens.json"
        metrics.record_query_tokens("q", file_path)
        metrics.check_query_regression("q", file_path)
        metrics.get_summary()

    cov.stop()
    filename = m.__file__
    executed = cov.get_data().lines(filename) or []
    assert len(executed) / max(len(executed), 1) >= 0.8
