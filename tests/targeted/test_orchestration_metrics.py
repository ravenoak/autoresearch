"""Tests for token recording and regression checks."""

import json
import sys
import types

sys.modules.setdefault(
    "pydantic_settings",
    types.SimpleNamespace(BaseSettings=object, CliApp=object, SettingsConfigDict=dict),
)

from autoresearch.orchestration.metrics import OrchestrationMetrics  # noqa: E402


def test_record_and_check_query_tokens(tmp_path):
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
