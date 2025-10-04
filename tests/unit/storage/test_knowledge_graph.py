from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Sequence

import networkx as nx
import pytest

from autoresearch.knowledge.graph import SessionGraphPipeline


class _StubStorageManager:
    """Minimal storage manager stub for knowledge graph export tests."""

    def __init__(self) -> None:
        self.persisted_claims: list[tuple[dict[str, Any], bool]] = []
        self.graph = nx.MultiDiGraph()
        self.context = SimpleNamespace(db_backend=None, rdf_store=None)

    def update_knowledge_graph(
        self,
        *,
        entities: Sequence[dict[str, Any]],
        relations: Sequence[dict[str, Any]],
        triples: Sequence[tuple[str, str, str]],
    ) -> None:
        for entity in entities:
            self.graph.add_node(entity["id"], label=entity.get("label"))
        for relation in relations:
            self.graph.add_edge(
                relation["subject_id"],
                relation["object_id"],
                key=relation.get("predicate", "related_to"),
                predicate=relation.get("predicate", "related_to"),
            )

    def get_knowledge_graph(self, *, create: bool = False) -> nx.MultiDiGraph:
        return self.graph

    @staticmethod
    def export_knowledge_graph_graphml() -> str:
        return "<graphml/>"

    @staticmethod
    def export_knowledge_graph_json() -> str:
        return "{\"nodes\": []}"

    def persist_claim(self, claim: dict[str, Any], partial_update: bool = False) -> None:
        self.persisted_claims.append((dict(claim), partial_update))


def test_ingest_persists_exports_and_updates_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Graph ingestion should persist provenance exports and flag availability."""

    stub_manager = _StubStorageManager()
    monkeypatch.setattr(
        SessionGraphPipeline,
        "_get_storage_manager",
        staticmethod(lambda: stub_manager),
    )

    pipeline = SessionGraphPipeline()
    snippets = [
        {
            "title": "Accuracy report",
            "snippet": (
                "Autoresearch was born in Paris. "
                "Autoresearch was born in Berlin. "
                "Autoresearch collaborated with Graph Systems."
            ),
            "url": "https://example.com/report",
        }
    ]

    summary = pipeline.ingest("Where is Autoresearch located?", snippets)

    assert stub_manager.persisted_claims, "Knowledge graph exports should persist as claims"
    claim_payload, partial_update = stub_manager.persisted_claims[0]
    assert not partial_update
    assert claim_payload["type"] == "knowledge_graph_export"
    assert claim_payload["attributes"]["graphml"] == "<graphml/>"
    assert claim_payload["attributes"]["graph_json"].startswith("{\"nodes\"")

    assert summary.exports == {"graphml": True, "graph_json": True}
    provenance_entry = summary.provenance[-1]
    assert provenance_entry["claim_id"] == claim_payload["id"]
    assert "graphml" in provenance_entry["formats"]
    assert summary.highlights["contradictions"], "Contradiction highlights should surface"
    contradiction_line = summary.highlights["contradictions"][0]
    assert "Autoresearch" in contradiction_line
    assert "born_in" in contradiction_line
    provenance_highlights = summary.highlights.get("provenance")
    assert provenance_highlights, "Provenance highlights should summarise records"
    assert "https://example.com/report" in provenance_highlights[0]
