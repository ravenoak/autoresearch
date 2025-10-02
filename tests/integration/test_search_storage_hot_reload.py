from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Sequence

import pytest
import tomli_w
import tomllib

from autoresearch.config.loader import ConfigLoader
from autoresearch.search import Search
from autoresearch.storage import StorageManager

SearchResults = Sequence[Mapping[str, object]]


@pytest.mark.slow
def test_search_storage_hot_reload(
    example_autoresearch_toml: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Search and storage should respect configuration reloads."""

    # Setup
    cfg_file: Path = example_autoresearch_toml
    cfg_file.write_text(tomli_w.dumps({"search": {"backends": ["b1"]}}))
    ConfigLoader.reset_instance()

    def fake_load(self: ConfigLoader) -> SimpleNamespace:
        data = tomllib.loads(cfg_file.read_text())
        return SimpleNamespace(
            search=SimpleNamespace(
                backends=data["search"]["backends"],
                context_aware=SimpleNamespace(enabled=False),
            )
        )

    monkeypatch.setattr(ConfigLoader, "load_config", fake_load, raising=False)
    loader = ConfigLoader()
    calls: list[str] = []
    stored: list[str] = []

    def backend1(query: str, max_results: int = 5) -> SearchResults:
        calls.append("b1")
        return [{"title": "t1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5) -> SearchResults:
        calls.append("b2")
        return [{"title": "t2", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", backend1)
    monkeypatch.setitem(Search.backends, "b2", backend2)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))

    def external_lookup(query: str, max_results: int = 5) -> SearchResults:
        cfg: SimpleNamespace = loader.config
        results: list[Mapping[str, object]] = []
        for b in cfg.search.backends:
            backend_results: SearchResults = Search.backends[b](query, max_results)
            results.extend(backend_results)
        for r in results:
            StorageManager.persist_claim(
                {"id": r["url"], "type": "source", "content": r["title"]}
            )
        return results

    monkeypatch.setattr(Search, "external_lookup", external_lookup)

    events: list[list[str]] = []

    def on_change(cfg: SimpleNamespace) -> None:
        events.append(cfg.search.backends)

    # Execute
    with loader.watching(on_change):
        loader.load_config()
        events.append(loader.config.search.backends)
        Search.external_lookup("q", max_results=1)
        cfg_file.write_text(tomli_w.dumps({"search": {"backends": ["b2"]}}))
        loader._config_time = 0
        time.sleep(0.1)
        Search.external_lookup("q", max_results=1)

    # Verify
    assert stored == ["u1", "u2"]
    assert calls == ["b1", "b2"]
    assert events[0] == ["b1"] and events[-1] == ["b2"]


@pytest.mark.slow
def test_search_storage_hot_reload_realistic(
    example_autoresearch_toml: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_file: Path = example_autoresearch_toml
    cfg_file.write_text(tomli_w.dumps({"search": {"backends": ["b1"]}}))
    ConfigLoader.reset_instance()

    def fake_load(self: ConfigLoader) -> SimpleNamespace:
        data = tomllib.loads(cfg_file.read_text())
        return SimpleNamespace(
            search=SimpleNamespace(
                backends=data["search"]["backends"],
                context_aware=SimpleNamespace(enabled=False),
            )
        )

    monkeypatch.setattr(ConfigLoader, "load_config", fake_load, raising=False)
    loader = ConfigLoader()
    calls: list[str] = []
    stored: list[str] = []

    def backend1(query: str, max_results: int = 5) -> SearchResults:
        calls.append("b1")
        return [{"title": "t1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5) -> SearchResults:
        calls.append("b2")
        return [{"title": "t2", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", backend1)
    monkeypatch.setitem(Search.backends, "b2", backend2)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))

    def external_lookup(query: str, max_results: int = 5) -> SearchResults:
        cfg: SimpleNamespace = loader.config
        results: list[Mapping[str, object]] = []
        for b in cfg.search.backends:
            backend_results: SearchResults = Search.backends[b](query, max_results)
            results.extend(backend_results)
        for r in results:
            StorageManager.persist_claim(
                {"id": r["url"], "type": "source", "content": r["title"]}
            )
        return results

    monkeypatch.setattr(Search, "external_lookup", external_lookup)

    with loader.watching(lambda cfg: None):
        loader.load_config()
        Search.external_lookup("Where is the Eiffel Tower?", max_results=1)
        cfg_file.write_text(tomli_w.dumps({"search": {"backends": ["b2"]}}))
        loader._config_time = 0
        time.sleep(0.1)
        Search.external_lookup("Where is the Eiffel Tower?", max_results=1)

    assert stored == ["u1", "u2"]
    assert calls == ["b1", "b2"]
