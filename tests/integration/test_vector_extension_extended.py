# mypy: ignore-errors
"""
Extended tests for the vector extension functionality.

This module contains additional tests for the vector extension functionality
to improve test coverage, focusing on edge cases, different vector dimensions,
and error handling in vector search.
"""

import logging
from pathlib import Path
from types import ModuleType
from typing import Mapping, Sequence

import duckdb  # noqa: E402
import pytest
from unittest.mock import patch

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.errors import StorageError  # noqa: E402
from autoresearch.extensions import VSSExtensionLoader  # noqa: E402
from autoresearch.storage import StorageManager  # noqa: E402
from autoresearch.storage_typing import DuckDBConnectionProtocol

try:
    _tmp_conn = duckdb.connect(database=":memory:")
    VSS_AVAILABLE = VSSExtensionLoader.verify_extension(_tmp_conn, verbose=False)
    _tmp_conn.close()
except Exception:
    VSS_AVAILABLE = False

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_vss,
    pytest.mark.skipif(not VSS_AVAILABLE, reason="VSS extension not available"),
]

logger = logging.getLogger(__name__)


def test_vector_search_with_different_dimensions(
    storage_manager: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test vector search with different embedding dimensions.

    This test verifies that:
    1. Claims with embeddings of different dimensions can be persisted
    2. Vector search works correctly with different dimensions
    """
    # Configure storage with vector extension enabled
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
        )
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Clear storage and prepare test data
    StorageManager.clear_all()
    conn: DuckDBConnectionProtocol = StorageManager.get_duckdb_conn()

    # Persist test claims with embeddings of different dimensions
    dimensions: list[int] = [2, 3, 4, 10]
    for dim in dimensions:
        # Create a vector of the specified dimension
        vec: list[float] = [float(i) / dim for i in range(dim)]
        StorageManager.persist_claim(
            {
                "id": f"dim{dim}",
                "type": "fact",
                "content": f"Dimension {dim}",
                "embedding": vec,
            }
        )

    # Verify claims were persisted
    for dim in dimensions:
        # Query the database directly to check if the claim exists
        result = conn.execute(
            f"SELECT id, content FROM nodes WHERE id = 'dim{dim}'"
        ).fetchone()
        assert result is not None, f"Claim with ID 'dim{dim}' should exist"
        assert result[0] == f"dim{dim}", f"Claim ID should be 'dim{dim}'"
        assert result[1] == f"Dimension {dim}", (
            f"Claim content should be 'Dimension {dim}'"
        )

        # Check that the embedding was stored with the correct dimension
        embedding = conn.execute(
            f"SELECT embedding FROM embeddings WHERE node_id = 'dim{dim}'"
        ).fetchone()
        assert embedding is not None, f"Embedding for 'dim{dim}' should exist"
        assert len(embedding[0]) == dim, f"Embedding dimension should be {dim}"

    # Test vector search with each dimension
    for dim in dimensions:
        # Create a query vector of the same dimension
        query_vec = [float(i) / dim for i in range(dim)]

        # Perform vector search
        results: Sequence[Mapping[str, object]] = StorageManager.vector_search(query_vec, k=1)

        # Verify that the correct claim was found
        assert results[0]["node_id"] == f"dim{dim}", (
            f"Vector search with dimension {dim} should find 'dim{dim}'"
        )


def test_vector_search_edge_cases(
    storage_manager: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test vector search edge cases.

    This test verifies that:
    1. Vector search works with zero vectors
    2. Vector search works with very large vectors
    3. Vector search works with very small k values
    4. Vector search works with large k values
    """
    # Configure storage with vector extension enabled
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
        )
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Clear storage and prepare test data
    StorageManager.clear_all()

    # Persist test claims with different vectors
    test_vectors: dict[str, list[float]] = {
        "zero": [0.0, 0.0, 0.0],
        "large": [1000.0, 2000.0, 3000.0],
        "small": [0.000001, 0.000002, 0.000003],
        "mixed": [0.0, 1.0, -1.0],
        "negative": [-1.0, -2.0, -3.0],
    }

    for name, vec in test_vectors.items():
        StorageManager.persist_claim(
            {
                "id": name,
                "type": "fact",
                "content": f"Vector {name}",
                "embedding": vec,
            }
        )

    # Test vector search with zero vector
    results: Sequence[Mapping[str, object]] = StorageManager.vector_search([0.0, 0.0, 0.0], k=1)
    assert results[0]["node_id"] == "zero", (
        "Vector search with zero vector should find 'zero'"
    )

    # Test vector search with large vector
    results = StorageManager.vector_search([1000.0, 2000.0, 3000.0], k=1)
    assert results[0]["node_id"] == "large", (
        "Vector search with large vector should find 'large'"
    )

    # Test vector search with small vector
    results = StorageManager.vector_search([0.000001, 0.000002, 0.000003], k=1)
    assert results[0]["node_id"] == "small", (
        "Vector search with small vector should find 'small'"
    )

    # Test vector search with k=1
    results = StorageManager.vector_search([0.0, 0.0, 0.0], k=1)
    assert len(results) == 1, "Vector search with k=1 should return 1 result"

    # Test vector search with k=10 (more than the number of vectors)
    results = StorageManager.vector_search([0.0, 0.0, 0.0], k=10)
    assert len(results) == 5, "Vector search with k=10 should return all 5 vectors"


def test_vector_search_error_handling(
    storage_manager: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test error handling in vector search.

    This test verifies that:
    1. Vector search handles invalid query vectors gracefully
    2. Vector search handles invalid k values gracefully
    3. Vector search handles database errors gracefully
    """
    # Configure storage with vector extension enabled
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
        )
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Clear storage and prepare test data
    StorageManager.clear_all()

    # Persist a test claim with a vector
    StorageManager.persist_claim(
        {
            "id": "test",
            "type": "fact",
            "content": "Test vector",
            "embedding": [0.1, 0.2, 0.3],
        }
    )

    # Test vector search with empty query vector
    with pytest.raises(Exception):
        StorageManager.vector_search([], k=1)

    # Test vector search with non-numeric query vector
    with pytest.raises(Exception):
        StorageManager.vector_search(["a", "b", "c"], k=1)

    # Test vector search with k=0
    with pytest.raises(Exception):
        StorageManager.vector_search([0.1, 0.2, 0.3], k=0)

    # Test vector search with negative k
    with pytest.raises(Exception):
        StorageManager.vector_search([0.1, 0.2, 0.3], k=-1)

    # Test vector search with database error
    with patch(
        "autoresearch.storage_backends.DuckDBStorageBackend.vector_search",
        side_effect=StorageError("Test error"),
    ):
        with pytest.raises(StorageError):
            StorageManager.vector_search([0.1, 0.2, 0.3], k=1)


def test_vector_search_with_no_embeddings(
    storage_manager: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test vector search when no embeddings are stored.

    This test verifies that:
    1. Vector search returns empty results when no embeddings are stored
    """
    # Configure storage with vector extension enabled
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
        )
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Clear storage
    StorageManager.clear_all()

    # Check if vector extension is available
    # Persist a claim without an embedding
    StorageManager.persist_claim(
        {
            "id": "no_embedding",
            "type": "fact",
            "content": "No embedding",
        }
    )

    # Test vector search
    results: Sequence[Mapping[str, object]] = StorageManager.vector_search([0.1, 0.2, 0.3], k=1)
    assert len(results) == 0, (
        "Vector search with no embeddings should return empty results"
    )
