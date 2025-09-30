"""Tests for typed orchestration utility helpers."""

from __future__ import annotations

from autoresearch.models import QueryResponse
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.utils import (
    MetricsSnapshot,
    TokenUsageSnapshot,
    calculate_result_confidence,
)


def build_response(**overrides: object) -> QueryResponse:
    base: dict[str, object] = {
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


def test_graph_metrics_payload_is_sanitized() -> None:
    metrics = OrchestrationMetrics()
    metadata = {
        "ingestion": {
            "entity_count": "3",
            "relation_count": 4,
            "seconds": "1.25",
            "storage_latency": {
                "persist": {"duckdb": "2.5", "rdf": -1},
                "load": [0.125, "oops"],
            },
        },
        "paths": [["node-a", 2]],
    }

    metrics.record_graph_build(metadata, summary={"provenance": ["ref"]})

    assert metrics.graph_ingestions
    record = metrics.graph_ingestions[-1]
    latency = record["storage_latency"]
    assert latency["persist.duckdb"] == 2.5
    assert latency["persist.rdf"] == 0.0
    assert latency["load[0]"] == 0.125
    assert latency["load[1]"] == 0.0

    summary = metrics.get_summary()["graph_ingestion"]
    latest = summary["latest"]
    assert latest["entity_count"] == 3.0
    assert latest["storage_latency"] == latency
