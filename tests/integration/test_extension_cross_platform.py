import duckdb
import pytest
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.extensions import VSSExtensionLoader

pytestmark = [pytest.mark.slow, pytest.mark.requires_vss]


def test_extension_path_normalized(tmp_path, monkeypatch):
    ext_file = tmp_path / "sub" / "vss.duckdb_extension"
    ext_file.parent.mkdir()
    ext_file.write_text("dummy")
    win_path = str(ext_file).replace("/", "\\")

    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            vector_extension_path=win_path,
            duckdb_path=str(tmp_path / "db.duckdb"),
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    class DummyConn:
        def __init__(self):
            self.commands = []

        def execute(self, sql, *args):
            self.commands.append(sql)
            return self

        def fetchone(self):
            return ["1"]

    dummy = DummyConn()
    monkeypatch.setattr(duckdb, "connect", lambda path: dummy)
    monkeypatch.setattr(
        VSSExtensionLoader, "verify_extension", lambda c, verbose=False: True
    )

    def fake_load(conn):
        VSSExtensionLoader.verify_extension(conn, verbose=False)
        return True

    monkeypatch.setattr(VSSExtensionLoader, "load_extension", fake_load)

    backend = DuckDBStorageBackend()
    backend.setup(db_path=str(tmp_path / "db.duckdb"))

    assert any(ext_file.as_posix() in cmd for cmd in dummy.commands)
