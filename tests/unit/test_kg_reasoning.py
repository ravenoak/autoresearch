import sys
from types import ModuleType

import pytest
import rdflib

from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import StorageError
from autoresearch.kg_reasoning import run_ontology_reasoner, query_with_reasoning


def _mock_config(reasoner: str) -> ConfigModel:
    return ConfigModel.model_construct(storage=StorageConfig(ontology_reasoner=reasoner))


def _patch_config(monkeypatch, reasoner: str) -> None:
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: _mock_config(reasoner))
    ConfigLoader()._config = None


def test_run_ontology_reasoner_owlrl(monkeypatch):
    g = rdflib.Graph()
    g.add((rdflib.URIRef("http://ex/s"), rdflib.URIRef("http://ex/p"), rdflib.URIRef("http://ex/o")))
    _patch_config(monkeypatch, "owlrl")
    run_ontology_reasoner(g)


def test_run_ontology_reasoner_external(monkeypatch):
    called = {}

    def dummy(store):
        called["ok"] = True

    mod = ModuleType("dummy_mod")
    mod.func = dummy
    monkeypatch.setitem(sys.modules, "dummy_mod", mod)
    g = rdflib.Graph()
    _patch_config(monkeypatch, "dummy_mod:func")
    run_ontology_reasoner(g)
    assert called.get("ok") is True


def test_run_ontology_reasoner_external_error(monkeypatch):
    def fail(store):
        raise ValueError("boom")

    mod = ModuleType("bad_mod")
    mod.run = fail
    monkeypatch.setitem(sys.modules, "bad_mod", mod)
    g = rdflib.Graph()
    _patch_config(monkeypatch, "bad_mod:run")
    with pytest.raises(StorageError):
        run_ontology_reasoner(g)


def test_query_with_reasoning(monkeypatch):
    g = rdflib.Graph()
    s = rdflib.URIRef("http://ex/s")
    p = rdflib.URIRef("http://ex/p")
    o = rdflib.URIRef("http://ex/o")
    g.add((s, p, o))
    _patch_config(monkeypatch, "owlrl")
    q = f"SELECT ?o WHERE {{ <{s}> <{p}> ?o }}"
    res = list(query_with_reasoning(g, q))
    assert len(res) == 1
    assert res[0][0] == o
