"""Tests for RDF persistence functionality.

This module contains tests for the RDF persistence functionality of the storage
system, verifying that claims are properly stored in the RDF store and can be
retrieved.

For a standalone demo of idempotent setup and teardown, see
``scripts/oxigraph_backend_sim.py``.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from importlib.machinery import ModuleSpec

import pytest
import rdflib

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.errors import StorageError
from autoresearch.storage import StorageContext, StorageManager
from autoresearch.storage_typing import JSONDict


@pytest.fixture(autouse=True)
def cleanup_rdf_store() -> Iterator[None]:
    """Clean up the RDF store after each test.

    This fixture ensures that the RDF store is properly cleaned up
    after each test, preventing test pollution and resource leaks.
    """
    # Setup is done in the test
    yield

    # Teardown
    context: StorageContext = StorageManager.context
    if context.rdf_store is not None:
        context.rdf_store = None
    ConfigLoader.reset_instance()
    import autoresearch.storage as storage_module

    storage_module._cached_config = None


@pytest.mark.slow
def test_rdf_persistence(storage_manager, tmp_path, monkeypatch):
    """Test that claims are properly persisted to the RDF store.

    This test verifies that when a claim is persisted using the StorageManager,
    it is properly stored in the RDF store and can be retrieved using RDF queries.
    """
    # Setup
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(
            rdf_backend="oxigraph",
            rdf_path=str(tmp_path / "nested" / "rdf_store"),
        )
    )

    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader.new_for_tests()
    import autoresearch.storage as storage_module

    storage_module._cached_config = None

    claim: JSONDict = {
        "id": "n1",
        "type": "fact",
        "content": "c",
        "attributes": {"verified": True},
    }

    # Execute
    StorageManager.persist_claim(claim)

    # Verify
    store = StorageManager.get_rdf_store()
    subj = rdflib.URIRef("urn:claim:n1")
    results = list(store.triples((subj, None, None)))
    assert results, "Claim was not persisted to the RDF store"


def test_oxigraph_backend_initializes(tmp_path, monkeypatch):
    """RDF store should use OxiGraph backend when configured."""
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(
            rdf_backend="oxigraph",
            rdf_path=str(tmp_path / "rdf_store"),
        )
    )

    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader.new_for_tests()

    StorageManager.teardown(remove_db=True)
    StorageManager.setup()

    StorageManager.get_rdf_store()
    assert StorageManager.get_rdf_backend_identifier() == "OxiGraph"


def test_oxrdflib_missing_plugin(tmp_path, monkeypatch):
    """Fail gracefully when oxrdflib is not installed."""
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(
            rdf_backend="oxigraph",
            rdf_path=str(tmp_path / "rdf_store"),
        )
    )

    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader.new_for_tests()

    def fake_find_spec(name: str) -> ModuleSpec | None:
        if name == "oxrdflib":
            return None
        return importlib.util.find_spec(name)

    monkeypatch.setattr("autoresearch.storage_backends.importlib.util.find_spec", fake_find_spec)

    StorageManager.teardown(remove_db=True)
    with pytest.raises(StorageError):
        StorageManager.setup()


@pytest.mark.slow
def test_memory_backend_initializes(tmp_path, monkeypatch):
    """RDF store should use in-memory backend when configured."""
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(
            rdf_backend="memory",
            rdf_path=str(tmp_path / "rdf_store"),
        )
    )

    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader.new_for_tests()

    StorageManager.teardown(remove_db=True)
    StorageManager.setup()

    store = StorageManager.get_rdf_store()
    assert store.store.__class__.__name__ == "IOMemory"
