from __future__ import annotations

from pytest import MonkeyPatch
from unittest.mock import MagicMock, patch

from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader


def _basic_config() -> ConfigModel:
    return ConfigModel(storage=StorageConfig(), ram_budget_mb=0)


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
