from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from scripts.storage_concurrency_sim import SimulationResult, _run as concurrency_run

from autoresearch import storage as storage_module
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.storage_typing import JSONDict


def test_concurrency_benchmark() -> None:
    result: SimulationResult = concurrency_run(threads=2, items=3)
    assert result.remaining_nodes == 0
    assert result.setup_calls == 1
    assert result.setup_failures == 0
    assert result.unique_contexts == 1


def _ram_budget_run(items: int) -> int:
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(
            duckdb_path=":memory:", ontology_reasoner_max_triples=1
        ),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    loader = ConfigLoader.new_for_tests()
    loader._config = cfg

    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()
    StorageManager.state = st
    StorageManager.context = ctx

    original: Callable[[], float] = StorageManager._current_ram_mb

    def fake_current_ram_mb() -> float:
        return 1000.0

    cast(Any, StorageManager)._current_ram_mb = staticmethod(fake_current_ram_mb)
    original_reasoner: Callable[[Any, str | None], None] = getattr(
        storage_module, "run_ontology_reasoner"
    )

    def noop_reasoner(store: Any, engine: str | None = None) -> None:
        return None

    setattr(storage_module, "run_ontology_reasoner", noop_reasoner)
    try:
        StorageManager.setup(db_path=":memory:", context=ctx, state=st)
        for i in range(items):
            claim: JSONDict = {"id": f"c{i}", "type": "fact", "content": "c"}
            StorageManager.persist_claim(claim)
            StorageManager._enforce_ram_budget(cfg.ram_budget_mb)
        remaining: int = StorageManager.get_graph().number_of_nodes()
    finally:
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        cast(Any, StorageManager)._current_ram_mb = staticmethod(original)
        setattr(storage_module, "run_ontology_reasoner", original_reasoner)
        ConfigLoader.reset_instance()

    return remaining


def test_ram_budget_benchmark() -> None:
    remaining: int = _ram_budget_run(items=5)
    assert remaining == 0
