"""Integration tests for ontology reasoning utilities."""

import rdflib
import pytest

from tests.optional_imports import import_or_skip

from autoresearch.storage import StorageManager, teardown
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.kg_reasoning import register_reasoner


def _simple_rdfs(graph: rdflib.Graph) -> None:
    """Tiny RDFS subclass reasoner used for integration tests."""

    for subj, obj in graph.subject_objects(rdflib.RDF.type):
        for _s, _p, super_cls in graph.triples((obj, rdflib.RDFS.subClassOf, None)):
            graph.add((subj, rdflib.RDF.type, super_cls))


@pytest.fixture(autouse=True)
def cleanup():
    yield
    teardown(remove_db=True)
    ConfigLoader.reset_instance()


def _configure(tmp_path, monkeypatch, engine: str = "simple_rdfs"):
    cfg = ConfigModel(
        storage=StorageConfig(
            rdf_backend="memory",
            rdf_path=str(tmp_path / "rdf"),
            ontology_reasoner=engine,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader.new_for_tests()
    register_reasoner("simple_rdfs")(_simple_rdfs)


def test_reasoning_infers_subclass(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    StorageManager.setup()

    onto = tmp_path / "onto.ttl"
    onto.write_text(
        """
@prefix ex: <http://example.com/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
ex:A rdfs:subClassOf ex:B .
"""
    )
    StorageManager.load_ontology(str(onto))

    store = StorageManager.get_rdf_store()
    store.add(
        (
            rdflib.URIRef("http://example.com/x"),
            rdflib.RDF.type,
            rdflib.URIRef("http://example.com/A"),
        )
    )

    StorageManager.apply_ontology_reasoning()

    res = StorageManager.query_rdf(
        "ASK { <http://example.com/x> a <http://example.com/B> }"
    )
    assert res.askAnswer, "Subclass inference failed"


def test_visualization_creates_file(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    StorageManager.setup()

    import_or_skip("matplotlib")

    store = StorageManager.get_rdf_store()
    store.add(
        (
            rdflib.URIRef("urn:a"),
            rdflib.URIRef("urn:rel"),
            rdflib.URIRef("urn:b"),
        )
    )

    out = tmp_path / "graph.png"
    StorageManager.visualize_rdf(str(out))
    assert out.exists() and out.stat().st_size > 0
