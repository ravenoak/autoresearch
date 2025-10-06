import time

import pytest
import rdflib
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import autoresearch.kg_reasoning as kr
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.errors import StorageError


def _mock_config(
    reasoner: str, timeout: float | None = None, max_triples: int | None = None
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


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.unit
@given(
    triples=st.sets(
        st.tuples(
            st.text(min_size=1, max_size=5),
            st.text(min_size=1, max_size=5),
            st.text(min_size=1, max_size=5),
        ),
        max_size=5,
    )
)
def test_reasoner_preserves_triples(monkeypatch, triples):
    g = rdflib.Graph()
    for s, p, o in triples:
        g.add((rdflib.URIRef(s), rdflib.URIRef(p), rdflib.URIRef(o)))
    before = len(g)

    def add_one(store: rdflib.Graph) -> None:
        store.add(
            (
                rdflib.URIRef("urn:a"),
                rdflib.URIRef("urn:b"),
                rdflib.URIRef("urn:c"),
            )
        )

    monkeypatch.setitem(kr._REASONER_PLUGINS, "add_one", add_one)
    _patch_config(monkeypatch, "add_one")
    kr.run_ontology_reasoner(g)
    assert len(g) >= before


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.unit
@given(timeout=st.floats(min_value=0.0, max_value=0.05))
def test_reasoner_timeout(monkeypatch, timeout):
    g = rdflib.Graph()

    def slow(store: rdflib.Graph) -> None:
        time.sleep(timeout + 0.05)

    monkeypatch.setitem(kr._REASONER_PLUGINS, "slow_prop", slow)
    _patch_config(monkeypatch, "slow_prop", timeout=timeout)
    with pytest.raises(StorageError):
        kr.run_ontology_reasoner(g)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.unit
@given(
    count=st.integers(min_value=0, max_value=5),
    limit=st.integers(min_value=1, max_value=5),
)
def test_reasoner_respects_triple_limit(monkeypatch, count, limit):
    g = rdflib.Graph()
    for i in range(count):
        g.add(
            (
                rdflib.URIRef(f"urn:s{i}"),
                rdflib.URIRef("urn:p"),
                rdflib.URIRef("urn:o"),
            )
        )

    called = {}

    def mark(store: rdflib.Graph) -> None:
        called["hit"] = True

    monkeypatch.setitem(kr._REASONER_PLUGINS, "marker", mark)
    _patch_config(monkeypatch, "marker", max_triples=limit)
    kr.run_ontology_reasoner(g)
    if count <= limit:
        assert "hit" in called
    else:
        assert "hit" not in called
