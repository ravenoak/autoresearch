from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.extensions import VSSExtensionLoader
from autoresearch.storage import StorageManager
import pytest
from pathlib import Path


def test_storage_setup_with_stub_extension(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """StorageManager.setup succeeds when using a stubbed VSS extension."""
    stub = tmp_path / "extensions" / "vss.duckdb_extension"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.touch()
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "kg.duckdb"),
            vector_extension_path=str(stub),
        )
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(VSSExtensionLoader, "load_extension", lambda conn: False)
    ConfigLoader()._config = None

    StorageManager.clear_all()
    StorageManager.setup()
    assert not StorageManager.has_vss()
