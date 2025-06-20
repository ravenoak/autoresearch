"""Integration tests for ontology reasoning utilities."""

import rdflib
import pytest

from autoresearch.storage import StorageManager, teardown
from autoresearch.config import ConfigModel, StorageConfig, ConfigLoader


@pytest.fixture(autouse=True)
def cleanup():
    yield
    teardown(remove_db=True)
    if hasattr(ConfigLoader, "_instance"):
        ConfigLoader._instance = None


def _configure(tmp_path, monkeypatch):
    cfg = ConfigModel(
        storage=StorageConfig(
            rdf_backend="memory",
            rdf_path=str(tmp_path / "rdf"),
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None


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

    pytest.importorskip("matplotlib")

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

