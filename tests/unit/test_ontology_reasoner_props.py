import rdflib
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import autoresearch.kg_reasoning as kr
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from typing import Any


def _mock_config(reasoner: str) -> ConfigModel:
    return ConfigModel.model_construct(
        storage=StorageConfig(ontology_reasoner=reasoner)
    )


def _patch_config(monkeypatch: pytest.MonkeyPatch, reasoner: str) -> None:
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(reasoner),
    )
    ConfigLoader()._config = None


def _transitive_closure(store: rdflib.Graph) -> None:
    """Add transitive closure for the predicate ``urn:p``."""
    p = rdflib.URIRef("urn:p")
    edges = {(s, o) for s, _, o in store.triples((None, p, None))}
    changed = True
    while changed:
        changed = False
        for a, b in list(edges):
            for c, d in list(edges):
                if b == c and (a, d) not in edges:
                    edges.add((a, d))
                    changed = True
    for a, b in edges:
        store.add((a, p, b))


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.unit
@given(
    triples=st.sets(
        st.tuples(
            st.text(min_size=1, max_size=4),
            st.text(min_size=1, max_size=4),
        ),
        max_size=5,
    )
)
def test_reasoner_reaches_closure(monkeypatch: pytest.MonkeyPatch, triples: Any) -> None:
    """Running the reasoner twice does not add new triples."""
    g = rdflib.Graph()
    p = rdflib.URIRef("urn:p")
    for s, o in triples:
        g.add((rdflib.URIRef(f"urn:{s}"), p, rdflib.URIRef(f"urn:{o}")))
    before = len(g)
    monkeypatch.setitem(kr._REASONER_PLUGINS, "closure", _transitive_closure)
    _patch_config(monkeypatch, "closure")
    kr.run_ontology_reasoner(g)
    after_first = len(g)
    kr.run_ontology_reasoner(g)
    assert len(g) == after_first >= before
