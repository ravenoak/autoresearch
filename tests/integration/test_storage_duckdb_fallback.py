from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.config import ConfigLoader


def test_duckdb_vss_fallback(tmp_path, monkeypatch):
    """Storage operates without VSS when the extension is missing."""
    ConfigLoader()._config = None
    cfg = ConfigLoader().config
    cfg.storage.duckdb_path = str(tmp_path / "kg.duckdb")
    cfg.storage.vector_extension = True

    st = StorageState()
    ctx = StorageContext()

    monkeypatch.setattr(
        "autoresearch.extensions.VSSExtensionLoader.load_extension", lambda _c: False
    )

    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)
    try:
        assert not StorageManager.has_vss()
        assert StorageManager.vector_search([0.0]) == []
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        ConfigLoader()._config = None
