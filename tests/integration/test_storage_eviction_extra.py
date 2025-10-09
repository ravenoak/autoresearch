# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path
from threading import Thread

from _pytest.monkeypatch import MonkeyPatch

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.orchestration import metrics
from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.storage_typing import JSONDict


def test_concurrent_eviction(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )

    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader()._config = None

    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()

    def high_ram() -> float:
        return 1000.0

    monkeypatch.setattr(StorageManager, "_current_ram_mb", high_ram)
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    start: float = metrics.EVICTION_COUNTER._value.get()

    def persist(idx: int) -> None:
        claim: JSONDict = {"id": f"c{idx}", "type": "fact", "content": "c"}
        StorageManager.persist_claim(claim)

    threads: list[Thread] = [Thread(target=persist, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert StorageManager.get_graph().number_of_nodes() == 0
    assert metrics.EVICTION_COUNTER._value.get() >= start + 5

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
