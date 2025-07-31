import duckdb
import pytest
from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader

pytestmark = [pytest.mark.slow, pytest.mark.requires_vss]


def test_vector_search_uses_params(tmp_path, monkeypatch):
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
            vector_search_batch_size=64,
            vector_search_timeout_ms=5000,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    commands = []

    class DummyConn:
        def execute(self, sql, *args):
            commands.append(sql)
            return self

        def fetchall(self):
            return [("n1", [0.1, 0.2])]

        def fetchone(self):
            return ["1"]

    dummy = DummyConn()
    monkeypatch.setattr(duckdb, "connect", lambda p: dummy)
    monkeypatch.setattr(
        "autoresearch.extensions.VSSExtensionLoader.verify_extension", lambda c, verbose=False: True
    )

    StorageManager.setup(str(tmp_path / "kg.duckdb"))
    StorageManager.vector_search([0.1, 0.2], k=1)

    assert any("vss_search_batch_size=64" in cmd for cmd in commands)
    assert any("query_timeout_ms=5000" in cmd for cmd in commands)
