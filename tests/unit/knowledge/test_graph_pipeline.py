from __future__ import annotations

from typing import Any

import networkx as nx
import pytest

from autoresearch.config import ConfigLoader, ConfigModel
from autoresearch.knowledge import SessionGraphPipeline
from autoresearch.storage import StorageManager
from tests.typing_helpers import make_storage_context


class DummyBackend:
    def __init__(self) -> None:
        self.entities: list[list[dict[str, Any]]] = []
        self.relations: list[list[dict[str, Any]]] = []

    def persist_graph_entities(self, payload: list[dict[str, Any]]) -> None:
        self.entities.append(list(payload))

    def persist_graph_relations(self, payload: list[dict[str, Any]]) -> None:
        self.relations.append(list(payload))


class DummyRDFStore:
    def __init__(self) -> None:
        self.triples: list[tuple[Any, Any, Any]] = []

    def add(self, triple: tuple[Any, Any, Any]) -> None:
        self.triples.append(triple)


@pytest.fixture(autouse=True)
def _reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    ConfigLoader.reset_instance()

    def _fake_load(self: ConfigLoader) -> ConfigModel:
        return ConfigModel()

    monkeypatch.setattr(ConfigLoader, "load_config", _fake_load)


def test_session_graph_pipeline_ingest_records_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = SessionGraphPipeline()

    backend = DummyBackend()
    rdf_store = DummyRDFStore()
    graph: nx.MultiDiGraph[Any] = nx.MultiDiGraph()
    context = make_storage_context(
        db_backend=backend,
        rdf_store=rdf_store,
        kg_graph=graph,
    )
    StorageManager.context = context

    def _fake_get_graph(create: bool = False) -> nx.MultiDiGraph[Any]:
        return graph

    # Mock the backend methods directly since _persist_batch calls them
    monkeypatch.setattr(backend, "persist_graph_entities", lambda payload, namespace=None: None)
    monkeypatch.setattr(backend, "persist_graph_relations", lambda payload, namespace=None: None)
    monkeypatch.setattr(rdf_store, "add", lambda triple: None)

    summary = pipeline.ingest(
        "Where was Marie Curie's collaborator born?",
        [
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
        ],
    )

    # Check that entities and relations were extracted
    summary_dict = summary.to_dict()
    assert summary_dict["entity_count"] > 0, "Expected entities to be extracted"
    assert summary_dict["relation_count"] > 0, "Expected relations to be extracted"
    assert summary_dict["provenance"], "Provenance records should be captured"
    assert set(summary_dict["storage_latency"]) == {"duckdb_seconds", "rdf_seconds"}


def test_session_graph_pipeline_neighbors_uses_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = SessionGraphPipeline()

    graph: nx.MultiDiGraph[Any] = nx.MultiDiGraph()
    graph.add_node("kg:marie", label="Marie Curie")
    graph.add_node("kg:pierre", label="Pierre Curie")
    graph.add_edge(
        "kg:marie",
        "kg:pierre",
        key="collaborated_with",
        predicate="collaborated_with",
    )

    StorageManager.context = make_storage_context(kg_graph=graph)

    def _fake_get_graph(create: bool = False) -> nx.MultiDiGraph[Any]:
        return graph

    monkeypatch.setattr(StorageManager, "get_knowledge_graph", staticmethod(_fake_get_graph))

    neighbors = pipeline.neighbors("Marie Curie", direction="out", limit=3)
    assert neighbors, "Neighbors should be returned for known entity"
    assert neighbors[0]["predicate"] == "collaborated_with"
    assert neighbors[0]["object"] == "Pierre Curie"
