import networkx as nx
from unittest.mock import MagicMock
import pytest

from autoresearch.storage import StorageManager
from autoresearch.errors import StorageError
from typing import Any


def test_persist_claim_db_failure(mock_storage_components: Any, claim_factory: Any, assert_error: Any) -> None:
    """Persisting a claim fails when the database backend raises an error."""
    mock_graph = nx.DiGraph()
    mock_rdf = MagicMock()
    mock_db = MagicMock()
    mock_db.persist_claim.side_effect = StorageError("Failed to persist claim to DuckDB")

    with mock_storage_components(graph=mock_graph, db_backend=mock_db, rdf=mock_rdf):
        with pytest.raises(StorageError) as excinfo:
            StorageManager.persist_claim(claim_factory.create_claim("c1"))

    assert_error(excinfo, "Failed to persist claim to DuckDB", has_cause=False)
