import builtins
import importlib
import sys
from types import ModuleType

import pytest
import rdflib
import threading
from typing import Any

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
    monkeypatch: pytest.MonkeyPatch,
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


def test_run_ontology_reasoner_owlrl(monkeypatch: pytest.MonkeyPatch) -> None:
    g: rdflib.Graph = rdflib.Graph()
    g.add(
        (
            rdflib.URIRef("http://ex/s"),
            rdflib.URIRef("http://ex/p"),
            rdflib.URIRef("http://ex/o"),
        )
    )
    _patch_config(monkeypatch, "owlrl")
    run_ontology_reasoner(g)


def test_register_reasoner_adds_plugin() -> None:
    import autoresearch.kg_reasoning as kr

    @register_reasoner("unit_test")
    def _plugin(store: rdflib.Graph) -> None:  # pragma: no cover - no logic needed
        pass

    assert kr._REASONER_PLUGINS["unit_test"] is _plugin
    kr._REASONER_PLUGINS.pop("unit_test", None)


def test_run_ontology_reasoner_external(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, bool] = {}

    def dummy(store: rdflib.Graph) -> None:
        called["ok"] = True

    mod = ModuleType("dummy_mod")
    setattr(mod, "func", dummy)
    monkeypatch.setitem(sys.modules, "dummy_mod", mod)
    g: rdflib.Graph = rdflib.Graph()
    _patch_config(monkeypatch, "dummy_mod:func")
    run_ontology_reasoner(g)
    assert called.get("ok") is True


def test_run_ontology_reasoner_invokes_plugin_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autoresearch.kg_reasoning as kr

    calls: list[bool] = []

    @register_reasoner("once")
    def _once(store: rdflib.Graph) -> None:
        calls.append(True)

    g: rdflib.Graph = rdflib.Graph()
    _patch_config(monkeypatch, "once")
    run_ontology_reasoner(g)
    assert calls == [True]
    kr._REASONER_PLUGINS.pop("once", None)


def test_run_ontology_reasoner_preserves_triple_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autoresearch.kg_reasoning as kr

    @register_reasoner("adder")
    def _adder(store: rdflib.Graph) -> None:
        store.add(
            (
                rdflib.URIRef("urn:s2"),
                rdflib.URIRef("urn:p"),
                rdflib.URIRef("urn:o"),
            )
        )

    g: rdflib.Graph = rdflib.Graph()
    g.add((rdflib.URIRef("urn:s1"), rdflib.URIRef("urn:p"), rdflib.URIRef("urn:o")))
    before = len(g)
    _patch_config(monkeypatch, "adder")
    run_ontology_reasoner(g)
    assert len(g) >= before
    kr._REASONER_PLUGINS.pop("adder", None)


def test_run_ontology_reasoner_external_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(store: rdflib.Graph) -> None:
        raise ValueError("boom")

    mod = ModuleType("bad_mod")
    setattr(mod, "run", fail)
    monkeypatch.setitem(sys.modules, "bad_mod", mod)
    g: rdflib.Graph = rdflib.Graph()
    _patch_config(monkeypatch, "bad_mod:run")
    with pytest.raises(StorageError):
        run_ontology_reasoner(g)


def test_query_with_reasoning(monkeypatch: pytest.MonkeyPatch) -> None:
    g: rdflib.Graph = rdflib.Graph()
    s = rdflib.URIRef("http://ex/s")
    p = rdflib.URIRef("http://ex/p")
    o = rdflib.URIRef("http://ex/o")
    g.add((s, p, o))
    _patch_config(monkeypatch, "owlrl")
    q = f"SELECT ?o WHERE {{ <{s}> <{p}> ?o }}"
    res = list(query_with_reasoning(g, q))
    assert len(res) == 1
    assert res[0][0] == o


def test_run_ontology_reasoner_without_owlrl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "owlrl", raising=False)
    import autoresearch.kg_reasoning as kr

    kr = importlib.reload(kr)
    g: rdflib.Graph = rdflib.Graph()
    _patch_config(monkeypatch, "owlrl")
    kr.run_ontology_reasoner(g)


def test_run_ontology_reasoner_reload_without_owlrl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autoresearch.kg_reasoning as module

    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any):
        if name == "owlrl":
            raise ImportError("owlrl missing during test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    module = importlib.reload(module)
    assert isinstance(module.owlrl.DeductiveClosure, type)

    g = rdflib.Graph()
    _patch_config(monkeypatch, "owlrl")
    module.run_ontology_reasoner(g)

    monkeypatch.setattr(builtins, "__import__", real_import)
    module = importlib.reload(module)
    globals()["run_ontology_reasoner"] = module.run_ontology_reasoner
    globals()["query_with_reasoning"] = module.query_with_reasoning
    globals()["register_reasoner"] = module.register_reasoner


def test_run_ontology_reasoner_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import autoresearch.kg_reasoning as kr

    def slow(store: rdflib.Graph) -> None:
        threading.Event().wait()

    monkeypatch.setitem(kr._REASONER_PLUGINS, "slow", slow)
    g: rdflib.Graph = rdflib.Graph()
    _patch_config(monkeypatch, "slow", timeout=0)
    with pytest.raises(StorageError) as excinfo:
        run_ontology_reasoner(g)
    assert "timed out" in str(excinfo.value).lower()


def test_run_ontology_reasoner_keyboard_interrupt(monkeypatch):
    def boom(store):
        raise KeyboardInterrupt()

    mod = ModuleType("kb_mod")
    setattr(mod, "run", boom)
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


def test_run_ontology_reasoner_unknown(monkeypatch):
    g = rdflib.Graph()
    _patch_config(monkeypatch, "does_not_exist")
    with pytest.raises(StorageError) as excinfo:
        run_ontology_reasoner(g)
    assert "unknown ontology reasoner" in str(excinfo.value).lower()
