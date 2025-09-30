"""Unit tests for RDF update utilities."""

from unittest.mock import MagicMock, patch

from autoresearch.storage import StorageManager


def _patch_reasoner():
    return patch("autoresearch.storage.run_ontology_reasoner")


def test_update_rdf_claim_replace() -> None:
    store = MagicMock()
    store.triples.return_value = [("s", "p", "o"), ("s", "p2", "o2")]
    with patch.object(StorageManager.context, "rdf_store", store), _patch_reasoner() as r:
        with patch("rdflib.URIRef", side_effect=lambda x: x), patch(
            "rdflib.Literal", side_effect=lambda x: x
        ):
            StorageManager._update_rdf_claim(
                {"id": "x", "attributes": {"a": 1}}, partial_update=False
            )

    # ensure existing triples were removed and new one added
    assert store.remove.call_count == 2
    store.add.assert_called_once_with(("urn:claim:x", "urn:prop:a", 1))
    r.assert_called_once_with(store)


def test_update_rdf_claim_partial() -> None:
    store = MagicMock()
    store.triples.return_value = [("s", "p", "o")]
    with patch.object(StorageManager.context, "rdf_store", store), _patch_reasoner() as r:
        with patch("rdflib.URIRef", side_effect=lambda x: x), patch(
            "rdflib.Literal", side_effect=lambda x: x
        ):
            StorageManager._update_rdf_claim(
                {"id": "x", "attributes": {"b": 2}}, partial_update=True
            )

    # ensure no removal happened for partial update
    store.remove.assert_not_called()
    store.add.assert_called_once_with(("urn:claim:x", "urn:prop:b", 2))
    r.assert_called_once_with(store)
