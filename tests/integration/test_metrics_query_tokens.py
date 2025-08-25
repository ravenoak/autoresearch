"""Integration test for recording query token usage."""

from __future__ import annotations

from pathlib import Path

from autoresearch.orchestration.metrics import OrchestrationMetrics


def test_record_query_tokens(tmp_path: Path) -> None:
    m = OrchestrationMetrics()
    m.record_tokens("Agent", 1, 2)
    out = tmp_path / "tokens.json"
    m.record_query_tokens("Q", out)
    assert "Q" in out.read_text()
