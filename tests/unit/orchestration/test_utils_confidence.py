"""Tests for typed orchestration utility helpers."""

from __future__ import annotations

from autoresearch.models import QueryResponse
from autoresearch.orchestration.utils import MetricsSnapshot, TokenUsageSnapshot, calculate_result_confidence


def build_response(**overrides: object) -> QueryResponse:
    base = {
        "answer": "result",
        "citations": [],
        "reasoning": [],
        "metrics": {},
    }
    base.update(overrides)
    return QueryResponse(**base)


def test_metrics_snapshot_parses_token_usage() -> None:
    metrics = {
        "token_usage": {"total": 50, "max_tokens": 100},
        "errors": ["timeout"],
    }

    snapshot = MetricsSnapshot.from_mapping(metrics)

    assert isinstance(snapshot.token_usage, TokenUsageSnapshot)
    assert snapshot.token_usage.utilization_ratio == 0.5
    assert snapshot.errors == ("timeout",)


def test_confidence_adjusts_with_metrics_payload() -> None:
    response = build_response(
        metrics={
            "token_usage": {"total": 45, "max_tokens": 90},
            "errors": ["transient"],
        }
    )

    confidence = calculate_result_confidence(response)

    expected_base = 0.5  # no citations or reasoning provided
    expected_with_tokens = expected_base + 0.1
    expected_with_errors = expected_with_tokens - 0.1

    assert confidence == expected_with_errors
