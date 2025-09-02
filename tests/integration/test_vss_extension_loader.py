import duckdb
import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.extensions import VSSExtensionLoader
from autoresearch.storage import StorageManager, StorageState
from autoresearch.storage_backends import DuckDBStorageBackend

pytestmark = [pytest.mark.requires_vss]


class DummyConnection:
    """Simple stand-in for a DuckDB connection."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def execute(self, query: str):  # noqa: D401
        """Record queries and simulate LOAD vss failures."""
        if "LOAD vss" in query and self.fail:
            raise duckdb.Error("LOAD vss failed")
        return self

    def close(self) -> None:  # pragma: no cover - trivial
        pass


def _setup_storage(monkeypatch: pytest.MonkeyPatch, conn: DummyConnection) -> None:
    """Configure StorageManager to use a mocked DuckDB connection."""
    monkeypatch.setattr(duckdb, "connect", lambda *_: conn)
    monkeypatch.setattr(
        DuckDBStorageBackend, "_create_tables", lambda self, skip_migrations=False: None
    )
    monkeypatch.setattr(DuckDBStorageBackend, "create_hnsw_index", lambda self: None)

    def mock_load_extension(c: DummyConnection) -> bool:
        try:
            c.execute("LOAD vss")
            return True
        except duckdb.Error:
            return False

    monkeypatch.setattr(VSSExtensionLoader, "load_extension", mock_load_extension)

    cfg = ConfigModel(storage=StorageConfig(vector_extension=True))
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    StorageManager.state = StorageState()
    StorageManager.context = StorageManager.state.context
    StorageManager.setup(db_path=":memory:")


def test_has_vss_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """StorageManager.has_vss returns True when LOAD vss succeeds."""
    conn = DummyConnection()
    _setup_storage(monkeypatch, conn)
    try:
        assert StorageManager.has_vss() is True
    finally:
        StorageManager.teardown(remove_db=True)


def test_has_vss_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """StorageManager.has_vss returns False when LOAD vss fails."""
    conn = DummyConnection(fail=True)
    _setup_storage(monkeypatch, conn)
    try:
        assert StorageManager.has_vss() is False
    finally:
        StorageManager.teardown(remove_db=True)
