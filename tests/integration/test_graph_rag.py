from __future__ import annotations

from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestration_utils import ScoutGateDecision
from autoresearch.orchestration.state import QueryState
from autoresearch.search.context import SearchContext
from autoresearch.storage import StorageManager


def _reset_storage() -> None:
    StorageManager.teardown(remove_db=True)
    StorageManager.setup(db_path=":memory:")


def test_graph_rag_ingestion_contradictions_and_metrics() -> None:
    """Graph ingestion should surface neighbors, contradictions, and telemetry."""

    _reset_storage()
    metrics = OrchestrationMetrics()

    with SearchContext.temporary_instance() as context:
        query = "Where is Gotham located and which city is it the capital of?"
        results = [
            {
                "title": "Gotham capital record",
                "snippet": "Gotham is the capital of Arkham.",
                "url": "https://example.org/gotham-arkham",
            },
            {
                "title": "Alternate capital claim",
                "snippet": "Gotham is the capital of Bludhaven.",
                "url": "https://example.org/gotham-bludhaven",
            },
            {
                "title": "Arkham location",
                "snippet": "Arkham is located in New Jersey.",
                "url": "https://example.org/arkham-location",
            },
            {
                "title": "Bludhaven location",
                "snippet": "Bludhaven is located in Delaware.",
                "url": "https://example.org/bludhaven-location",
            },
        ]

        context.add_to_history(query, results)

        neighbors = context.get_graph_neighbors_for_nodes(
            ["Gotham", "Arkham", "Bludhaven"], direction="both", limit=6
        )
        assert "Gotham" in neighbors
        gotham_targets = {edge.get("target") for edge in neighbors["Gotham"]}
        assert {"Arkham", "Bludhaven"}.issubset(gotham_targets)

        stage_meta = context.get_graph_stage_metadata()
        ingestion = stage_meta.get("ingestion", {})
        assert ingestion.get("entity_count", 0.0) >= 3
        assert ingestion.get("relation_count", 0.0) >= 3
        assert ingestion.get("seconds", 0.0) >= 0.0
        assert stage_meta.get("paths"), "Graph metadata should surface multi-hop paths"

        contradictions_meta = stage_meta.get("contradictions", {})
        contradiction_items = contradictions_meta.get("items", [])
        assert contradiction_items, "Contradiction items should be captured"
        assert contradictions_meta.get("weighted_score", 0.0) > 0.0

        summary = context.get_graph_summary()
        assert summary.get("contradictions"), "Summary should include contradictions"

        state = QueryState(query=query)
        assert context.apply_scout_metadata(state)
        scout_stage = state.metadata.get("scout_stage", {})
        graph_meta = scout_stage.get("graph")
        assert graph_meta, "Planner metadata should include graph payload"
        assert graph_meta.get("neighbors"), "Planner metadata should expose neighbors"

        decision = ScoutGateDecision(
            should_debate=False,
            target_loops=1,
            heuristics={
                "graph_contradiction": float(
                    contradictions_meta.get("weighted_score", 0.0)
                )
            },
            thresholds={"graph_contradiction": 0.1},
            reason="telemetry_test",
            tokens_saved=0,
            rationales={},
            telemetry={
                "coverage": {},
                "retrieval_confidence": {},
                "contradiction_total": float(
                    contradictions_meta.get("weighted_score", 0.0)
                ),
                "contradiction_samples": len(contradiction_items),
                "graph": graph_meta,
            },
        )
        metrics.record_gate_decision(decision)

    StorageManager.teardown(remove_db=True)

    metrics_summary = metrics.get_summary()
    graph_metrics = metrics_summary.get("graph_ingestion", {})
    assert graph_metrics.get("runs") == 1

    latest = graph_metrics.get("latest", {})
    assert latest.get("entity_count", 0.0) >= 3
    assert latest.get("relation_count", 0.0) >= 3
    assert latest.get("contradiction_count", 0.0) >= 1
    assert latest.get("neighbor_edge_count", 0.0) >= 2
    assert latest.get("path_count", 0.0) >= 1

    neighbor_sample = latest.get("neighbor_sample", {})
    assert neighbor_sample, "Metrics should retain a neighbor sample"
    assert any(node == "Gotham" for node in neighbor_sample)
    gotham_sample = neighbor_sample.get("Gotham") or []
    if gotham_sample:
        gotham_neighbor_targets = {edge.get("target") for edge in gotham_sample}
        assert {"Arkham", "Bludhaven"}.issubset(gotham_neighbor_targets)

    totals = graph_metrics.get("totals", {})
    assert totals.get("entity_count", 0.0) >= latest.get("entity_count", 0.0)
