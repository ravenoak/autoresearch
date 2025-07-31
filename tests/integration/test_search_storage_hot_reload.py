import time
import tomli_w
import tomllib

from types import SimpleNamespace

from autoresearch.config import ConfigLoader
from autoresearch.search import Search
from autoresearch.storage import StorageManager


def test_search_storage_hot_reload(tmp_path, monkeypatch):
    """Search and storage should respect configuration reloads."""

    # Setup
    monkeypatch.chdir(tmp_path)
    cfg_file = tmp_path / "autoresearch.toml"
    cfg_file.write_text(tomli_w.dumps({"search": {"backends": ["b1"]}}))
    ConfigLoader.reset_instance()

    def fake_load(self):
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

    def backend1(query: str, max_results: int = 5):
        calls.append("b1")
        return [{"title": "t1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5):
        calls.append("b2")
        return [{"title": "t2", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", backend1)
    monkeypatch.setitem(Search.backends, "b2", backend2)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))

    def external_lookup(query: str, max_results: int = 5):
        cfg = loader.config
        results = []
        for b in cfg.search.backends:
            results.extend(Search.backends[b](query, max_results))
        return results

    monkeypatch.setattr(Search, "external_lookup", external_lookup)

    events: list[list[str]] = []

    def on_change(cfg):
        events.append(cfg.search.backends)

    # Execute
    with loader.watching(on_change):
        loader.load_config()
        Search.external_lookup("q", max_results=1)
        StorageManager.persist_claim({"id": "c1", "type": "fact", "content": "v"})
        cfg_file.write_text(tomli_w.dumps({"search": {"backends": ["b2"]}}))
        time.sleep(0.1)
        Search.external_lookup("q", max_results=1)

    # Verify
    assert stored == ["c1"]
    assert calls == ["b1", "b2"]
    assert events and events[-1] == ["b2"]
