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

    update_payload: dict[str, Any] = {}

    def _fake_update(
        *,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        triples: list[tuple[Any, Any, Any]],
    ) -> None:
        update_payload["entities"] = entities
        update_payload["relations"] = relations
        update_payload["triples"] = triples
        for entity in entities:
            graph.add_node(entity["id"], label=entity.get("label", entity["id"]))
        for relation in relations:
            graph.add_edge(
                relation["subject_id"],
                relation["object_id"],
                key=relation["predicate"],
                predicate=relation["predicate"],
                **relation.get("provenance", {}),
            )
        backend.persist_graph_entities(entities)
        backend.persist_graph_relations(relations)
        for triple in triples:
            rdf_store.add(triple)

    def _fake_get_graph(create: bool = False) -> nx.MultiDiGraph[Any]:
        return graph

    monkeypatch.setattr(StorageManager, "update_knowledge_graph", staticmethod(_fake_update))
    monkeypatch.setattr(StorageManager, "get_knowledge_graph", staticmethod(_fake_get_graph))

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

    assert update_payload["entities"], "Expected entities to be persisted"
    assert update_payload["relations"], "Expected relations to be persisted"
    assert update_payload["triples"], "Expected triples to be generated"
    summary_dict = summary.to_dict()
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
