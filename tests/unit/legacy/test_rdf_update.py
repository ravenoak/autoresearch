# mypy: ignore-errors
"""Unit tests for RDF update utilities."""

import pytest
from unittest.mock import MagicMock, patch

from autoresearch.storage import StorageManager


def _patch_reasoner():
    return patch("autoresearch.storage.run_ontology_reasoner")


@pytest.mark.xfail(reason="RDF store mocking issue - needs proper rdflib integration")
def test_update_rdf_claim_replace():
    store = MagicMock()
    store.triples.return_value = [("s", "p", "o"), ("s", "p2", "o2")]
    # Mock the graph.add method to avoid rdflib type issues
    store.add.return_value = store

    # Mock the StorageManager state properly
    state_mock = MagicMock()
    state_mock.context.rdf_store = store

    with patch.object(StorageManager, "state", state_mock), _patch_reasoner() as r:
        StorageManager._update_rdf_claim(
            {"id": "x", "attributes": {"a": 1}}, "test_namespace", partial_update=False
        )

    # ensure existing triples were removed and new one added
    assert store.remove.call_count == 2
    store.add.assert_called_once()
    # Check that the expected triple was passed (ignoring exact rdflib object types)
    call_args = store.add.call_args[0][0]
    assert len(call_args) == 3
    assert "test_namespace:x" in str(call_args[0])
    assert "prop:a" in str(call_args[1])
    assert "1" in str(call_args[2])
    r.assert_called_once_with(store)


@pytest.mark.xfail(reason="RDF store mocking issue - needs proper rdflib integration")
def test_update_rdf_claim_partial():
    store = MagicMock()
    store.triples.return_value = [("s", "p", "o")]
    # Mock the graph.add method to avoid rdflib type issues
    store.add.return_value = store

    # Mock the StorageManager state properly
    state_mock = MagicMock()
    state_mock.context.rdf_store = store

    with patch.object(StorageManager, "state", state_mock), _patch_reasoner() as r:
        StorageManager._update_rdf_claim(
            {"id": "x", "attributes": {"b": 2}}, "test_namespace", partial_update=True
        )

    # ensure no removal happened for partial update
    store.remove.assert_not_called()
    store.add.assert_called_once()
    # Check that the expected triple was passed (ignoring exact rdflib object types)
    call_args = store.add.call_args[0][0]
    assert len(call_args) == 3
    assert "test_namespace:x" in str(call_args[0])
    assert "prop:b" in str(call_args[1])
    assert "2" in str(call_args[2])
    r.assert_called_once_with(store)
