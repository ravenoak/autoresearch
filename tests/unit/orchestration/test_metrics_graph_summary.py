from __future__ import annotations

from autoresearch.orchestration.metrics import OrchestrationMetrics
from __future__ import annotations

from autoresearch.orchestration.metrics import OrchestrationMetrics


def test_graph_summary_uses_typed_floats() -> None:
    metrics = OrchestrationMetrics()
    metadata = {
        "ingestion": {
            "entity_count": "2",
            "relation_count": 3,
            "seconds": "0.25",
            "storage_latency": {
                "persist": "4.5",
                "load": float("nan"),
            },
        },
        "contradictions": {
            "items": [
                {"subject": "a", "predicate": "p", "objects": ["b", 5]},
                {"subject": "c", "predicate": "q", "objects": ()},
            ],
            "raw_score": "1.5",
            "weighted_score": "2.5",
            "weight": 3,
        },
        "neighbors": {
            "node-1": [
                {"target": "x", "predicate": "p", "direction": "out"},
                {"target": "y", "predicate": "q", "direction": "in"},
            ]
        },
        "paths": [["s", "t"]],
        "similarity": {
            "raw_score": "0.5",
            "weighted_score": "0.25",
            "weight": "0.75",
        },
    }
    metrics.record_graph_build(metadata, summary={"provenance": [1, 2]})

    summary = metrics.get_summary()["graph_ingestion"]
    assert summary["runs"] == 1

    totals = summary["totals"]
    assert totals["entity_count"] == 2.0
    assert totals["relation_count"] == 3.0
    assert totals["contradiction_count"] == 2.0
    assert totals["provenance_count"] == 2.0
    assert totals["ingestion_seconds"] == 0.25
    assert totals["similarity_score"] == 0.5

    latency_totals = summary["totals_storage_latency"]
    assert latency_totals == {"persist": 4.5, "load": 0.0}

    averages = summary["averages"]
    assert averages["entity_count"] == 2.0
    assert averages["storage_latency"] == {"persist": 4.5, "load": 0.0}

    latest = summary["latest"]
    assert latest["entity_count"] == 2.0
    assert latest["storage_latency"] == {"persist": 4.5, "load": 0.0}
    assert latest["provenance_count"] == 2.0
    assert latest["contradiction_sample"][0]["objects"] == ["b", "5"]
    assert list(latest["neighbor_sample"].keys()) == ["node-1"]


def test_graph_build_skips_empty_payload() -> None:
    metrics = OrchestrationMetrics()
    metrics.record_graph_build({"ingestion": {"entity_count": 0, "relation_count": 0}})
    assert metrics.graph_ingestions == []


def test_graph_ingestion_saved_payload_is_sanitized() -> None:
    metrics = OrchestrationMetrics()
    metadata = {
        "ingestion": {
            "entity_count": "1",
            "relation_count": -5,
            "seconds": "0.75",
            "storage_latency": {"persist": -1, "load": float("nan")},
        },
        "paths": (("a", "b"),),
        "similarity": {"raw_score": float("inf"), "weighted_score": 3, "weight": None},
    }

    metrics.record_graph_build(metadata, summary={"provenance": [object()]})

    assert metrics.graph_ingestions
    record = metrics.graph_ingestions[-1]
    assert record["entity_count"] == 1.0
    assert record["relation_count"] == 0.0
    assert record["ingestion_seconds"] == 0.75
    assert record["storage_latency"] == {"persist": 0.0, "load": 0.0}
    assert record["similarity_score"] == 0.0
    assert record["similarity_weighted"] == 3.0
    assert record["similarity_weight"] == 0.0
    assert record["path_count"] == 1.0
    assert record["provenance_count"] == 1.0
