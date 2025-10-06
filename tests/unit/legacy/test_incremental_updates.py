# mypy: ignore-errors
from __future__ import annotations

import pytest
from pytest import MonkeyPatch
from unittest.mock import MagicMock, patch

from autoresearch.storage import (
    StorageContext,
    StorageManager,
    StorageState,
    initialize_storage,
)
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader


def _basic_config() -> ConfigModel:
    return ConfigModel(storage=StorageConfig(), ram_budget_mb=0)


@pytest.fixture(autouse=True)
def _deterministic_bootstrap_guard() -> None:
    """Ensure storage bootstrap reuses state and skips migrations."""

    context = StorageContext()
    state = StorageState(context=context)
    backend = MagicMock()
    backend.get_connection.return_value = object()
    backend._create_tables = MagicMock()
    context.db_backend = backend
    context.rdf_store = MagicMock()

    initialize_storage(context=context, state=state)
    graph_first = context.graph
    kg_first = context.kg_graph

    assert graph_first is not None
    assert kg_first is not None
    backend._create_tables.assert_called_once_with(skip_migrations=True)

    backend._create_tables.reset_mock()
    initialize_storage(context=context, state=state)
    assert context.graph is graph_first
    assert context.kg_graph is kg_first
    backend._create_tables.assert_called_once_with(skip_migrations=True)


def test_refresh_vector_index_calls_backend(monkeypatch: MonkeyPatch) -> None:
    backend: MagicMock = MagicMock()
    monkeypatch.setattr(StorageManager.context, "db_backend", backend, raising=False)
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)

    StorageManager.refresh_vector_index()

    backend.refresh_hnsw_index.assert_called_once()


def test_persist_claim_triggers_index_refresh(monkeypatch: MonkeyPatch) -> None:
    backend: MagicMock = MagicMock()
    graph: MagicMock = MagicMock()
    store: MagicMock = MagicMock()
    monkeypatch.setattr(StorageManager.context, "db_backend", backend, raising=False)
    monkeypatch.setattr(StorageManager.context, "graph", graph, raising=False)
    monkeypatch.setattr(StorageManager.context, "rdf_store", store, raising=False)
    monkeypatch.setattr(StorageManager, "_enforce_ram_budget", lambda budget: None)
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: _basic_config())
    ConfigLoader()._config = None

    called: dict[str, bool] = {}

    def refresh() -> None:
        called["r"] = True

    monkeypatch.setattr(StorageManager, "refresh_vector_index", refresh)

    StorageManager.persist_claim(
        {"id": "n1", "type": "fact", "content": "c", "embedding": [0.1]}
    )

    assert called.get("r") is True


def test_update_rdf_claim_wrapper(monkeypatch: MonkeyPatch) -> None:
    store: MagicMock = MagicMock()
    monkeypatch.setattr(StorageManager.context, "rdf_store", store, raising=False)
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)

    with patch("autoresearch.storage.StorageManager._update_rdf_claim") as upd:
        StorageManager.update_rdf_claim({"id": "x"}, partial_update=True)
        upd.assert_called_once()
