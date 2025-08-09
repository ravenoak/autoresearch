import importlib
import sys
from types import ModuleType

import pytest
import rdflib

import time

from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import StorageError
from autoresearch.kg_reasoning import (
    run_ontology_reasoner,
    query_with_reasoning,
    register_reasoner,
)


def _mock_config(
    reasoner: str,
    timeout: float | None = None,
    max_triples: int | None = None,
) -> ConfigModel:
    return ConfigModel.model_construct(
        storage=StorageConfig(
            ontology_reasoner=reasoner,
            ontology_reasoner_timeout=timeout,
            ontology_reasoner_max_triples=max_triples,
        )
    )


def _patch_config(
    monkeypatch,
    reasoner: str,
    timeout: float | None = None,
    max_triples: int | None = None,
) -> None:
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(reasoner, timeout, max_triples),
    )
    ConfigLoader()._config = None


def test_run_ontology_reasoner_owlrl(monkeypatch):
    g = rdflib.Graph()
    g.add(
        (
            rdflib.URIRef("http://ex/s"),
            rdflib.URIRef("http://ex/p"),
            rdflib.URIRef("http://ex/o"),
        )
    )
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


def test_run_ontology_reasoner_without_owlrl(monkeypatch):
    monkeypatch.delitem(sys.modules, "owlrl", raising=False)
    import autoresearch.kg_reasoning as kr

    kr = importlib.reload(kr)
    g = rdflib.Graph()
    _patch_config(monkeypatch, "owlrl")
    kr.run_ontology_reasoner(g)


def test_run_ontology_reasoner_timeout(monkeypatch):
    import autoresearch.kg_reasoning as kr

    def slow(store):
        time.sleep(0.2)

    monkeypatch.setitem(kr._REASONER_PLUGINS, "slow", slow)
    g = rdflib.Graph()
    _patch_config(monkeypatch, "slow", timeout=0.1)
    with pytest.raises(StorageError) as excinfo:
        run_ontology_reasoner(g)
    assert "timed out" in str(excinfo.value).lower()


def test_run_ontology_reasoner_keyboard_interrupt(monkeypatch):
    def boom(store):
        raise KeyboardInterrupt()

    mod = ModuleType("kb_mod")
    mod.run = boom
    monkeypatch.setitem(sys.modules, "kb_mod", mod)
    g = rdflib.Graph()
    _patch_config(monkeypatch, "kb_mod:run", timeout=1.0)
    with pytest.raises(StorageError) as excinfo:
        run_ontology_reasoner(g)
    assert "interrupted" in str(excinfo.value).lower()


def test_run_ontology_reasoner_skips_when_limit_exceeded(monkeypatch, caplog):
    called = {}

    @register_reasoner("dummy_limit")
    def _dummy(store):  # pragma: no cover - executed only if limit ignored
        called["hit"] = True

    g = rdflib.Graph()
    g.add(
        (
            rdflib.URIRef("urn:s"),
            rdflib.URIRef("urn:p"),
            rdflib.URIRef("urn:o"),
        )
    )
    g.add(
        (
            rdflib.URIRef("urn:s2"),
            rdflib.URIRef("urn:p"),
            rdflib.URIRef("urn:o"),
        )
    )

    _patch_config(monkeypatch, "dummy_limit", max_triples=1)

    with caplog.at_level("WARNING"):
        run_ontology_reasoner(g)

    assert "Skipping ontology reasoning" in caplog.text
    assert "hit" not in called

    # cleanup plugin registry
    import autoresearch.kg_reasoning as kr

    kr._REASONER_PLUGINS.pop("dummy_limit", None)
