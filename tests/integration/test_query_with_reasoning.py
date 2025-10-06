# mypy: ignore-errors
import rdflib
from pathlib import Path

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageManager
from autoresearch.storage_typing import GraphProtocol, RDFQueryResultProtocol


def _configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ConfigModel(
        storage=StorageConfig(rdf_backend="memory", rdf_path=str(tmp_path / "rdf"))
    )
    cfg.api.role_permissions["anonymous"] = ["query"]

    def load_config_override(self: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_override)
    ConfigLoader()._config = None


def test_query_with_reasoning_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    store: GraphProtocol = StorageManager.get_rdf_store()
    store.add(
        (
            rdflib.URIRef("http://example.com/x"),
            rdflib.RDF.type,
            rdflib.URIRef("http://example.com/A"),
        )
    )

    res: RDFQueryResultProtocol = StorageManager.query_with_reasoning(
        "ASK { <http://example.com/x> a <http://example.com/B> }", engine="owlrl"
    )
    assert res.askAnswer
