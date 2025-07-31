import logging
import pytest

from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.slow, pytest.mark.requires_vss]


def test_vector_search_with_real_duckdb(storage_manager, tmp_path, monkeypatch):
    """Test vector search functionality with a real DuckDB instance.

    This test verifies that:
    1. Claims with embeddings can be persisted
    2. If the vector extension is available, vector search works correctly
    3. If the vector extension is not available, basic storage still works
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
    conn = StorageManager.get_duckdb_conn()

    # Persist test claims with embeddings
    for idx, vec in enumerate([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]):
        StorageManager.persist_claim(
            {
                "id": f"n{idx}",
                "type": "fact",
                "content": str(idx),
                "embedding": vec,
            }
        )

    # Verify claims were persisted
    nodes = conn.execute("SELECT id FROM nodes").fetchall()
    assert len(nodes) == 3, "Claims should be persisted regardless of vector extension"

    # Check if vector extension is available
    try:
        # Check if the VSS extension is loaded
        result = conn.execute(
            "SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss'"
        ).fetchall()
        vector_extension_available = result and len(result) > 0
        if vector_extension_available:
            logger.info("Vector extension is available")
        else:
            logger.info("Vector extension is not available")
    except Exception as e:
        vector_extension_available = False
        logger.info(f"Vector extension is not available: {e}")

    # If vector extension is available, test vector search
    if vector_extension_available:
        # Check for indexes
        indexes = conn.execute(
            "SELECT index_name FROM duckdb_indexes() WHERE table_name='embeddings'"
        ).fetchall()

        if indexes:
            # Test vector search
            results = StorageManager.vector_search([0.0, 0.0], k=1)
            assert results[0]["node_id"] == "n0"
        else:
            logger.warning("Vector extension is available but no indexes were created")
            # Test that embeddings were stored even without indexes
            embeddings = conn.execute(
                "SELECT node_id, embedding FROM embeddings"
            ).fetchall()
            assert len(embeddings) == 3, (
                "Embeddings should be stored even without vector indexes")
    else:
        # Even without vector extension, embeddings should be stored
        embeddings = conn.execute(
            "SELECT node_id, embedding FROM embeddings"
        ).fetchall()
        assert len(embeddings) == 3, (
            "Embeddings should be stored even without vector extension")

        # Test that we can still retrieve claims by ID directly from the database
        for idx in range(3):
            # Query the database directly to check if the claim exists
            result = conn.execute(
                f"SELECT id, content FROM nodes WHERE id = 'n{idx}'"
            ).fetchone()
            assert result is not None, f"Claim with ID 'n{idx}' should exist"
            assert result[0] == f"n{idx}", f"Claim ID should be 'n{idx}'"
            assert result[1] == str(idx), f"Claim content should be '{idx}'"
