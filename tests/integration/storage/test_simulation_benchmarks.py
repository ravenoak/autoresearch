from __future__ import annotations

from scripts.storage_concurrency_sim import _run as concurrency_run

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch import storage as storage_module
from autoresearch.storage import StorageContext, StorageManager, StorageState


def test_concurrency_benchmark() -> None:
    remaining = concurrency_run(threads=2, items=3)
    assert remaining == 0


def _ram_budget_run(items: int) -> int:
    cfg = ConfigModel(
        storage=StorageConfig(
            duckdb_path=":memory:", ontology_reasoner_max_triples=1
        ),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    loader = ConfigLoader.new_for_tests()
    loader._config = cfg

    st = StorageState()
    ctx = StorageContext()
    StorageManager.state = st
    StorageManager.context = ctx

    original = StorageManager._current_ram_mb
    StorageManager._current_ram_mb = staticmethod(lambda: 1000)
    original_reasoner = storage_module.run_ontology_reasoner
    storage_module.run_ontology_reasoner = lambda *a, **k: None
    try:
        StorageManager.setup(db_path=":memory:", context=ctx, state=st)
        for i in range(items):
            StorageManager.persist_claim(
                {"id": f"c{i}", "type": "fact", "content": "c"}
            )
            StorageManager._enforce_ram_budget(cfg.ram_budget_mb)
        remaining = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        StorageManager._current_ram_mb = original  # type: ignore[assignment]
        storage_module.run_ontology_reasoner = original_reasoner
        ConfigLoader.reset_instance()

    return remaining


def test_ram_budget_benchmark() -> None:
    remaining = _ram_budget_run(items=5)
    assert remaining == 0
