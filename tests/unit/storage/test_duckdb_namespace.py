from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.storage_utils import namespace_table_suffix


def test_duckdb_persists_entities_by_namespace(tmp_path):
    backend = DuckDBStorageBackend()
    db_path = tmp_path / "namespaced.duckdb"
    backend.setup(db_path=str(db_path))
    try:
        backend.persist_graph_entities(
            [
                {
                    "id": "kg:foo",
                    "label": "Foo",
                    "type": "entity",
                    "attributes": {},
                }
            ],
            "alpha",
        )
        backend.persist_graph_entities(
            [
                {
                    "id": "kg:foo",
                    "label": "Foo",
                    "type": "entity",
                    "attributes": {},
                }
            ],
            "beta",
        )

        suffix_alpha = namespace_table_suffix("alpha")
        suffix_beta = namespace_table_suffix("beta")
        with backend.connection() as conn:
            tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
            assert f"kg_entities__{suffix_alpha}" in tables
            assert f"kg_entities__{suffix_beta}" in tables
            count_alpha = conn.execute(
                f"SELECT COUNT(*) FROM kg_entities__{suffix_alpha}"
            ).fetchone()[0]
            count_beta = conn.execute(
                f"SELECT COUNT(*) FROM kg_entities__{suffix_beta}"
            ).fetchone()[0]
        assert count_alpha == 1
        assert count_beta == 1
    finally:
        backend.close()
