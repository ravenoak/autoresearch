"""Unit tests for RDF update utilities."""

from unittest.mock import MagicMock, patch

import rdflib

from autoresearch.storage import StorageManager


def test_update_rdf_claim_replace():
    store = MagicMock()
    store.triples.return_value = [("s", "p", "o"), ("s", "p2", "o2")]
    with patch("autoresearch.storage._rdf_store", store):
        with patch("rdflib.URIRef", side_effect=lambda x: x), patch(
            "rdflib.Literal", side_effect=lambda x: x
        ):
            StorageManager._update_rdf_claim(
                {"id": "x", "attributes": {"a": 1}}, partial_update=False
            )

    # ensure existing triples were removed and new one added
    assert store.remove.call_count == 2
    store.add.assert_called_once_with(("urn:claim:x", "urn:prop:a", 1))


def test_update_rdf_claim_partial():
    store = MagicMock()
    store.triples.return_value = [("s", "p", "o")]
    with patch("autoresearch.storage._rdf_store", store):
        with patch("rdflib.URIRef", side_effect=lambda x: x), patch(
            "rdflib.Literal", side_effect=lambda x: x
        ):
            StorageManager._update_rdf_claim(
                {"id": "x", "attributes": {"b": 2}}, partial_update=True
            )

    # ensure no removal happened for partial update
    store.remove.assert_not_called()
    store.add.assert_called_once_with(("urn:claim:x", "urn:prop:b", 2))

