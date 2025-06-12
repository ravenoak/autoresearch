import rdflib
from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, StorageConfig, ConfigLoader


def test_rdf_persistence(storage_manager, tmp_path, monkeypatch):
    cfg = ConfigModel(
        storage=StorageConfig(
            rdf_backend="sqlite",
            rdf_path=str(tmp_path / "rdf_store"),
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    claim = {
        "id": "n1",
        "type": "fact",
        "content": "c",
        "attributes": {"verified": True},
    }
    StorageManager.persist_claim(claim)
    store = StorageManager.get_rdf_store()
    subj = rdflib.URIRef("urn:claim:n1")
    results = list(store.triples((subj, None, None)))
    assert results
