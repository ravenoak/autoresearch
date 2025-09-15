from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.config import ConfigLoader

from tests.optional_imports import import_or_skip

import_or_skip("pytest_benchmark")


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


def test_ram_budget_benchmark(tmp_path, monkeypatch, benchmark):
    ConfigLoader()._config = None
    cfg = ConfigLoader().config
    cfg.storage.duckdb_path = str(tmp_path / "kg.duckdb")
    cfg.ram_budget_mb = 1

    st = StorageState()
    ctx = StorageContext()
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 1000)
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    def run() -> None:
        StorageManager.persist_claim({"id": "b", "type": "fact", "content": "c"})

    benchmark(run)
    assert StorageManager.get_graph().number_of_nodes() == 0

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
