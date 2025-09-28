"""Integration tests validating knowledge graph construction."""

from __future__ import annotations

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
    StorageManager.teardown(remove_db=True)
