from __future__ import annotations

from pathlib import Path
from typing import cast

import rdflib

from autoresearch.storage_backends import init_rdf_store
from autoresearch.storage_typing import GraphProtocol, RDFTriple, to_json_dict


def test_to_json_dict_returns_copy() -> None:
    source = {"claim": "c1", "score": 0.9}
    cloned = to_json_dict(source)

    assert cloned == source
    cloned["score"] = 1.0
    assert source["score"] == 0.9


def test_init_rdf_store_supports_protocol(tmp_path: Path) -> None:
    store = init_rdf_store("memory", str(tmp_path / "rdf"))
    assert isinstance(store, GraphProtocol)

    triple = cast(
        RDFTriple,
        (
            rdflib.URIRef("urn:test:subject"),
            rdflib.URIRef("urn:test:predicate"),
            rdflib.Literal("value"),
        ),
    )
    store.add(triple)
    results = list(store.triples((None, None, None)))
    assert triple in results

    store.remove((None, None, None))
    assert list(store.triples((None, None, None))) == []
    assert len(store) == 0
