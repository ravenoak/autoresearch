import threading
from unittest.mock import MagicMock, patch

import threading
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import StorageError
from autoresearch.storage_backends import DuckDBStorageBackend


@pytest.fixture(autouse=True)
def reset_config_loader() -> Generator[None, None, None]:
    """Reset ``ConfigLoader`` before and after each test."""

    ConfigLoader.reset_instance()
    with patch("autoresearch.storage_backends.ConfigLoader") as mock_loader:
        mock_cfg = MagicMock()
        mock_cfg.config.storage.duckdb.path = "kg.duckdb"
        mock_loader.return_value.config = mock_cfg
        yield
    ConfigLoader.reset_instance()


def test_concurrent_setup_is_idempotent(tmp_path) -> None:
    """Concurrent setup calls create the schema only once."""

    backend = DuckDBStorageBackend()
    db_file = tmp_path / "test.duckdb"

    with patch("autoresearch.storage_backends.duckdb.connect", return_value=MagicMock()):
        with patch.object(DuckDBStorageBackend, "_create_tables") as create_tables:
            threads = [
                threading.Thread(target=backend.setup, kwargs={"db_path": str(db_file)})
                for _ in range(5)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert create_tables.call_count == 1

    backend.close()


def test_initialize_schema_version_failure(tmp_path) -> None:
    """Errors during schema version init raise ``StorageError``."""

    backend = DuckDBStorageBackend()

    with patch("autoresearch.storage_backends.duckdb.connect", return_value=MagicMock()):
        with patch.object(
            DuckDBStorageBackend, "_initialize_schema_version", side_effect=Exception("boom")
        ):
            with pytest.raises(StorageError):
                backend.setup(db_path=str(tmp_path / "db.duckdb"))


def test_persist_claims_concurrent(tmp_path) -> None:
    """Concurrent ``persist_claim`` calls remain thread safe."""

    backend = DuckDBStorageBackend()
    db_file = tmp_path / "claims.duckdb"

    with patch("autoresearch.storage_backends.duckdb.connect", return_value=MagicMock()):
        backend.setup(db_path=str(db_file))
        assert backend._conn is not None

        def store(idx: int) -> None:
            backend.persist_claim({"id": f"c{idx}"})

        threads = [threading.Thread(target=store, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert backend._conn.execute.call_count >= 5

    backend.close()
