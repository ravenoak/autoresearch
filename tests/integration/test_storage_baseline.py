from __future__ import annotations

from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.storage_typing import JSONDict


def test_ram_budget_respects_baseline(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Eviction uses memory delta from setup baseline."""
    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader()._config = None

    # Simulate high baseline memory before setup
    def high_baseline() -> float:
        return 1000.0

    monkeypatch.setattr("autoresearch.storage._process_ram_mb", high_baseline)
    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    # Avoid ontology reasoning delays during persistence
    def noop_reasoner(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr("autoresearch.storage.run_ontology_reasoner", noop_reasoner)

    # After setup memory increases slightly
    def slightly_higher() -> float:
        return 1001.0

    monkeypatch.setattr("autoresearch.storage._process_ram_mb", slightly_higher)
    claim: JSONDict = {"id": "a", "type": "fact", "content": "c"}
    StorageManager.persist_claim(claim)
    assert StorageManager.get_graph().number_of_nodes() == 1

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None


def test_eviction_respects_baseline_without_reasoner(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Eviction honors baseline when ontology reasoning is bypassed."""

    cfg: ConfigModel = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)
    ConfigLoader()._config = None

    # Establish baseline memory before setup
    def high_baseline() -> float:
        return 1000.0

    monkeypatch.setattr("autoresearch.storage._process_ram_mb", high_baseline)
    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    # Skip ontology reasoning to avoid unrelated failures
    def noop_reasoner(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr("autoresearch.storage.run_ontology_reasoner", noop_reasoner)

    # Sequence of RAM readings: under budget, then over budget, then back under
    ram_values: list[float] = [0.5, 2.0, 0.5]

    def fake_ram_mb() -> float:
        return ram_values.pop(0) if ram_values else 0.5

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram_mb)

    first_claim: JSONDict = {"id": "a", "type": "fact", "content": "a"}
    second_claim: JSONDict = {"id": "b", "type": "fact", "content": "b"}
    StorageManager.persist_claim(first_claim)
    StorageManager.persist_claim(second_claim)

    graph = StorageManager.get_graph()
    assert graph.number_of_nodes() == 1
    assert "b" in graph and "a" not in graph

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
