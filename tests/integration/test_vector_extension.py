import pytest

from autoresearch.storage import StorageManager
from autoresearch.config import (
    ConfigModel,
    StorageConfig,
    ConfigLoader,
)


def test_vector_search_with_real_duckdb(
    storage_manager, tmp_path, monkeypatch
):
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    StorageManager.clear_all()

    conn = StorageManager.get_duckdb_conn()
    for idx, vec in enumerate([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]):
        StorageManager.persist_claim(
            {
                "id": f"n{idx}",
                "type": "fact",
                "content": str(idx),
                "embedding": vec,
            }
        )

    indexes = conn.execute(
        "SELECT index_name FROM duckdb_indexes() WHERE table_name='embeddings'"
    ).fetchall()
    if not indexes:
        pytest.skip("vector extension not available")

    results = StorageManager.vector_search([0.0, 0.0], k=1)
    assert results[0]["node_id"] == "n0"
