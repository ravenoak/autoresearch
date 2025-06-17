"""Tests for RDF persistence functionality.

This module contains tests for the RDF persistence functionality of the storage system,
verifying that claims are properly stored in the RDF store and can be retrieved.
"""

import pytest
import rdflib
from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, StorageConfig, ConfigLoader


@pytest.fixture(autouse=True)
def cleanup_rdf_store():
    """Clean up the RDF store after each test.

    This fixture ensures that the RDF store is properly cleaned up
    after each test, preventing test pollution and resource leaks.
    """
    # Setup is done in the test
    yield

    # Teardown
    if hasattr(StorageManager, "_rdf_store"):
        StorageManager._rdf_store = None
    if hasattr(ConfigLoader, "_instance"):
        ConfigLoader._instance = None


def test_rdf_persistence(storage_manager, tmp_path, monkeypatch):
    """Test that claims are properly persisted to the RDF store.

    This test verifies that when a claim is persisted using the StorageManager,
    it is properly stored in the RDF store and can be retrieved using RDF queries.
    """
    # Setup
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

    # Execute
    StorageManager.persist_claim(claim)

    # Verify
    store = StorageManager.get_rdf_store()
    subj = rdflib.URIRef("urn:claim:n1")
    results = list(store.triples((subj, None, None)))
    assert results, "Claim was not persisted to the RDF store"


def test_sqlalchemy_backend_initializes(tmp_path, monkeypatch):
    """RDF store should use SQLAlchemy backend when configured."""
    cfg = ConfigModel(
        storage=StorageConfig(
            rdf_backend="sqlite",
            rdf_path=str(tmp_path / "rdf_store"),
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    StorageManager.teardown(remove_db=True)
    StorageManager.setup()

    store = StorageManager.get_rdf_store()
    assert store.store.name == "SQLAlchemy"
