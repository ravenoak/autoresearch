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


def test_init_rdf_store_memory_backend() -> None:
    """Test memory backend initialization."""
    store = init_rdf_store("memory", "/tmp/test")
    assert isinstance(store, GraphProtocol)
    # Memory backend should have identifier set
    assert hasattr(store, 'identifier')


def test_init_rdf_store_invalid_backend() -> None:
    """Test that invalid backend raises StorageError."""
    from autoresearch.errors import StorageError
    import pytest

    with pytest.raises(StorageError, match="Invalid RDF backend"):
        init_rdf_store("invalid", "/tmp/test")


def test_init_rdf_store_oxigraph_missing_driver(tmp_path: Path) -> None:
    """Test oxigraph backend with missing driver."""
    from autoresearch.errors import StorageError
    import pytest

    # Mock the import check to return None
    import importlib.util
    from typing import Any
    original_find_spec = importlib.util.find_spec

    def mock_find_spec(name: str, package: str | None = None) -> Any:
        if name == "oxrdflib":
            return None
        return original_find_spec(name, package)

    importlib.util.find_spec = mock_find_spec
    try:
        with pytest.raises(StorageError, match="OxiGraph driver not installed"):
            init_rdf_store("oxigraph", str(tmp_path / "rdf"))
    finally:
        importlib.util.find_spec = original_find_spec


def test_init_rdf_store_berkeleydb_creates_directory(tmp_path: Path) -> None:
    """Test berkeleydb backend creates parent directories."""
    from autoresearch.errors import StorageError
    import pytest

    db_path = tmp_path / "nested" / "dir" / "db"

    # BerkeleyDB plugin is not available, so it should raise StorageError
    with pytest.raises(StorageError, match="Missing RDF backend plugin"):
        init_rdf_store("berkeleydb", str(db_path))

    # But it should still create the directory structure before failing
    assert db_path.parent.exists()
