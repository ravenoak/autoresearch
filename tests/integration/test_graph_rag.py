from __future__ import annotations

from autoresearch.orchestration.state import QueryState
from autoresearch.search.context import SearchContext
from autoresearch.storage import StorageManager


def _reset_storage() -> None:
    StorageManager.teardown(remove_db=True)
    StorageManager.setup(db_path=":memory:")


def test_graph_rag_neighbors_metadata() -> None:
    """Search context should expose planner-ready graph metadata."""

    _reset_storage()
    with SearchContext.temporary_instance() as context:
        query = "How are Marie Curie and Pierre Curie related to Paris?"
        results = [
            {
                "title": "Marie Curie biography",
                "snippet": "Marie Curie discovered polonium with Pierre Curie.",
                "url": "https://example.org/curie",
            },
            {
                "title": "Pierre Curie",
                "snippet": "Pierre Curie was born in Paris and collaborated with Marie Curie.",
                "url": "https://example.org/pierre",
            },
        ]

        context.add_to_history(query, results)

        neighbors = context.get_graph_neighbors_for_nodes(
            ["Marie Curie", "Pierre Curie", "Paris"], direction="both", limit=5
        )
        assert "Marie Curie" in neighbors
        assert any(
            edge.get("target") == "Pierre Curie" for edge in neighbors["Marie Curie"]
        )
        assert "Pierre Curie" in neighbors

        stage_meta = context.get_graph_stage_metadata()
        ingestion = stage_meta.get("ingestion", {})
        assert ingestion.get("seconds", 0.0) >= 0.0
        assert ingestion.get("relation_count", 0.0) >= 2
        assert stage_meta.get("paths"), "Graph metadata should include multi-hop paths"

        state = QueryState(query=query)
        assert context.apply_scout_metadata(state)
        scout_stage = state.metadata.get("scout_stage", {})
        graph_meta = scout_stage.get("graph")
        assert graph_meta, "Graph metadata should be persisted for planner use"
        assert graph_meta.get("neighbors"), "Planner metadata should include neighbors"
        assert graph_meta.get("paths"), "Planner metadata should include paths"
        assert graph_meta.get("ingestion", {}).get("entity_count", 0.0) >= 2
    StorageManager.teardown(remove_db=True)
