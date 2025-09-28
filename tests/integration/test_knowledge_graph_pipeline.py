"""Integration tests validating knowledge graph construction."""

from __future__ import annotations

from autoresearch.orchestration.state import QueryState
from autoresearch.search.context import SearchContext
from autoresearch.storage import StorageManager


def _reset_storage() -> None:
    StorageManager.teardown(remove_db=True)
    StorageManager.setup(db_path=":memory:")


def test_knowledge_graph_multi_hop_paths() -> None:
    """Knowledge graph should surface multi-hop paths for multi-entity queries."""

    _reset_storage()
    with SearchContext.temporary_instance() as context:
        query = "Where was Marie Curie's collaborator born?"
        results = [
            {
                "title": "Marie Curie biography",
                "snippet": "Marie Curie discovered polonium with Pierre Curie.",
                "url": "https://example.org/curie",
            },
            {
                "title": "Pierre Curie",
                "snippet": "Pierre Curie was born in Paris.",
                "url": "https://example.org/pierre",
            },
        ]

        context.add_to_history(query, results)

        paths = context.graph_paths("Marie Curie", "Paris", max_depth=3)
        assert paths, "Expected at least one multi-hop path"
        flattened = {node for path in paths for node in path}
        assert {"Marie Curie", "Pierre Curie", "Paris"}.issubset(flattened)

        summary = context.get_graph_summary()
        assert summary["relation_count"] >= 2
        assert any(
            len(path) >= 3 and path[0] == "Marie Curie" and path[-1] == "Paris"
            for path in paths
        )
        stage_meta = context.get_graph_stage_metadata()
        assert stage_meta.get("paths"), "Graph stage metadata should expose paths"
        state = QueryState(query=query)
        applied = context.apply_scout_metadata(state)
        assert applied, "Scout metadata should be applied to query state"
        scout_stage = state.metadata.get("scout_stage", {})
        graph_meta = scout_stage.get("graph")
        assert graph_meta, "Graph metadata should be persisted in scout stage"
        assert graph_meta.get("paths"), "Planner metadata should include multi-hop paths"
        neighbors = graph_meta.get("neighbors", {})
        assert any(
            edge.get("target") == "Pierre Curie"
            for edge in neighbors.get("Marie Curie", [])
        ), "Expected Marie Curie neighbor to reference Pierre Curie"
        ingestion = graph_meta.get("ingestion", {})
        assert ingestion.get("seconds", 0.0) >= 0.0
        backend = StorageManager.context.db_backend
        assert backend is not None
        with backend.connection() as conn:
            entity_count = conn.execute("SELECT COUNT(*) FROM kg_entities").fetchone()[0]
            relation_count = conn.execute("SELECT COUNT(*) FROM kg_relations").fetchone()[0]
        assert entity_count > 0
        assert relation_count > 0
        rdf_store = StorageManager.context.rdf_store
        assert rdf_store is not None
        assert len(list(rdf_store.triples((None, None, None)))) > 0
    StorageManager.teardown(remove_db=True)


def test_knowledge_graph_contradiction_signal() -> None:
    """Contradictory relations should influence the contradiction signal."""

    _reset_storage()
    with SearchContext.temporary_instance() as context:
        query = "What city is Gotham the capital of?"
        results = [
            {
                "title": "Gotham in Arkham",
                "snippet": "Gotham is the capital of Arkham.",
                "url": "https://example.org/arkham",
            },
            {
                "title": "Gotham in Blüdhaven",
                "snippet": "Gotham is the capital of Bludhaven.",
                "url": "https://example.org/bludhaven",
            },
        ]

        context.add_to_history(query, results)

        signal = context.get_contradiction_signal()
        assert signal > 0.0
        summary = context.get_graph_summary()
        assert summary["contradictions"], "Expected contradiction entries in summary"
        state = QueryState(query=query)
        assert context.apply_scout_metadata(state)
        scout_stage = state.metadata.get("scout_stage", {})
        graph_meta = scout_stage.get("graph")
        assert graph_meta, "Contradiction metadata should be available"
        contradictions = graph_meta.get("contradictions", {})
        assert contradictions.get("items"), "Contradiction items should be surfaced"
        assert contradictions.get("raw_score") == summary["contradiction_score"]
        assert contradictions.get("weighted_score") == signal
        weight = contradictions.get("weight")
        assert isinstance(weight, float) and weight > 0.0
        neighbors = graph_meta.get("neighbors", {})
        assert "Gotham" in neighbors
        gotham_targets = {edge.get("object") for edge in neighbors["Gotham"]}
        assert {"Arkham", "Bludhaven"}.issubset(gotham_targets)
    StorageManager.teardown(remove_db=True)
