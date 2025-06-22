import rdflib
from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, StorageConfig, ConfigLoader


def _configure(tmp_path, monkeypatch):
    cfg = ConfigModel(
        storage=StorageConfig(rdf_backend="memory", rdf_path=str(tmp_path / "rdf"))
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None


def test_query_with_reasoning_engine(tmp_path, monkeypatch):
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

    res = StorageManager.query_with_reasoning(
        "ASK { <http://example.com/x> a <http://example.com/B> }", engine="owlrl"
    )
    assert res.askAnswer
