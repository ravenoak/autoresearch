# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

from _pytest.monkeypatch import MonkeyPatch

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]
else:  # pragma: no cover - typing fallback
    BenchmarkFixture = Any

from autoresearch.config import ConfigLoader
from autoresearch.storage import StorageContext, StorageManager, StorageState
from autoresearch.storage_typing import JSONDict

from tests.optional_imports import import_or_skip

import_or_skip("pytest_benchmark")


def test_duckdb_vss_fallback(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Storage operates without VSS when the extension is missing."""
    ConfigLoader()._config = None
    cfg = ConfigLoader().config
    cfg.storage.duckdb_path = str(tmp_path / "kg.duckdb")
    cfg.storage.vector_extension = True

    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()

    def disable_extension(_: object) -> bool:
        return False

    monkeypatch.setattr(
        "autoresearch.extensions.VSSExtensionLoader.load_extension", disable_extension
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


def test_ram_budget_benchmark(
    tmp_path: Path, monkeypatch: MonkeyPatch, benchmark: BenchmarkFixture
) -> None:
    ConfigLoader()._config = None
    cfg = ConfigLoader().config
    cfg.storage.duckdb_path = str(tmp_path / "kg.duckdb")
    cfg.ram_budget_mb = 1

    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()

    def high_ram() -> float:
        return 1000.0

    monkeypatch.setattr(StorageManager, "_current_ram_mb", high_ram)
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    def run() -> None:
        claim: JSONDict = {"id": "b", "type": "fact", "content": "c"}
        StorageManager.persist_claim(claim)

    benchmark(run)
    assert StorageManager.get_graph().number_of_nodes() == 0

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
