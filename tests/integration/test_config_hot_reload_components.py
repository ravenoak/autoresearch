import time
import tomli_w
import tomllib
from contextlib import contextmanager

import git
import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from tests.conftest import GITPYTHON_INSTALLED

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.requires_git,
    pytest.mark.skipif(not GITPYTHON_INSTALLED, reason="GitPython not installed"),
]


def make_agent(name, calls, stored):
    class DummyAgent:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config, **kwargs):
            Search.external_lookup("q", max_results=1)
            StorageManager.persist_claim({"id": self.name, "type": "fact", "content": self.name})
            calls.append(self.name)
            state.update({"results": {self.name: "ok"}, "claims": [{"id": self.name, "type": "fact", "content": self.name}]})
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {"results": {self.name: "ok"}}

    return DummyAgent(name)


def test_config_hot_reload_components(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = git.Repo.init(tmp_path)
    cfg_file = tmp_path / "autoresearch.toml"
    cfg_file.write_text(
        tomli_w.dumps(
            {
                "agents": ["AgentA"],
                "search": {"backends": ["b1"], "context_aware": {"enabled": False}},
            }
        )
    )
    repo.index.add([str(cfg_file)])
    repo.index.commit("init config")
    ConfigLoader.reset_instance()

    def fake_load(self):
        data = tomllib.loads(cfg_file.read_text())
        return ConfigModel.from_dict(
            {
                "agents": data["agents"],
                "loops": 1,
                "search": {
                    "backends": data["search"]["backends"],
                    "context_aware": {"enabled": False},
                },
            }
        )

    monkeypatch.setattr(ConfigLoader, "load_config", fake_load, raising=False)
    loader = ConfigLoader()

    calls: list[str] = []
    search_calls: list[str] = []
    stored: list[str] = []

    def backend1(query: str, max_results: int = 5):
        search_calls.append("b1")
        return [{"title": "t1", "url": "u1"}]

    def backend2(query: str, max_results: int = 5):
        search_calls.append("b2")
        return [{"title": "t2", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", backend1)
    monkeypatch.setitem(Search.backends, "b2", backend2)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name, llm_adapter=None: make_agent(name, calls, stored),
    )

    def external_lookup(query: str, max_results: int = 5):
        cfg = loader.config
        results = []
        for b in cfg.search.backends:
            results.extend(Search.backends[b](query, max_results))
        for r in results:
            StorageManager.persist_claim({"id": r["url"], "type": "source", "content": r["title"]})
        return results

    monkeypatch.setattr(Search, "external_lookup", external_lookup)

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    events: list[tuple[list[str], list[str]]] = []

    def on_change(cfg):
        events.append((cfg.agents, cfg.search.backends))

    with loader.watching(on_change):
        loader.load_config()
        events.append((loader.config.agents, loader.config.search.backends))
        Orchestrator.run_query("q", loader.config)
        cfg_file.write_text(
            tomli_w.dumps(
                {
                    "agents": ["AgentB"],
                    "search": {
                        "backends": ["b2"],
                        "context_aware": {"enabled": False},
                    },
                }
            )
        )
        repo.index.add([str(cfg_file)])
        repo.index.commit("update config")
        time.sleep(0.1)
        Orchestrator.run_query("q", loader.config)

    assert calls == ["AgentA", "AgentB"]
    assert search_calls == ["b1", "b2"]
    assert stored == ["u1", "AgentA", "u2", "AgentB"]
    assert events[0] == (["AgentA"], ["b1"]) and events[-1] == (["AgentB"], ["b2"])


def test_config_hot_reload_search_weights_and_storage(tmp_path, monkeypatch):
    """Search weights and storage settings should update without restart."""

    monkeypatch.chdir(tmp_path)
    repo = git.Repo.init(tmp_path)
    cfg_file = tmp_path / "autoresearch.toml"
    cfg_file.write_text(
        tomli_w.dumps(
            {
                "agents": ["AgentA"],
                "search": {
                    "backends": ["b1"],
                    "context_aware": {"enabled": False},
                    "semantic_similarity_weight": 0.7,
                    "bm25_weight": 0.2,
                    "source_credibility_weight": 0.1,
                },
                "storage": {"duckdb_path": "db1.duckdb"},
            }
        )
    )
    repo.index.add([str(cfg_file)])
    repo.index.commit("init config")
    ConfigLoader.reset_instance()

    def fake_load(self):
        data = tomllib.loads(cfg_file.read_text())
        return ConfigModel.from_dict(
            {
                "agents": data["agents"],
                "loops": 1,
                "search": {
                    "backends": data["search"]["backends"],
                    "context_aware": {"enabled": False},
                    "semantic_similarity_weight": data["search"][
                        "semantic_similarity_weight"
                    ],
                    "bm25_weight": data["search"]["bm25_weight"],
                    "source_credibility_weight": data["search"][
                        "source_credibility_weight"
                    ],
                },
                "storage": {"duckdb_path": data["storage"]["duckdb_path"]},
            }
        )

    monkeypatch.setattr(ConfigLoader, "load_config", fake_load, raising=False)
    loader = ConfigLoader()

    paths: list[str] = []
    weights: list[tuple[float, float, float]] = []

    monkeypatch.setattr(
        StorageManager,
        "persist_claim",
        lambda claim: paths.append(loader.config.storage.duckdb_path),
    )

    def external_lookup(query: str, max_results: int = 5):
        weights.append(
            (
                loader.config.search.semantic_similarity_weight,
                loader.config.search.bm25_weight,
                loader.config.search.source_credibility_weight,
            )
        )
        return [{"title": "t1", "url": "u1"}]

    monkeypatch.setattr(Search, "external_lookup", external_lookup)
    monkeypatch.setattr(
        AgentFactory, "get", lambda name, llm_adapter=None: make_agent(name, [], [])
    )

    events: list[tuple[float, str]] = []

    def on_change(cfg):
        events.append(
            (cfg.search.semantic_similarity_weight, cfg.storage.duckdb_path)
        )

    loader.watch_changes(on_change)
    loader.load_config()
    events.append(
        (loader.config.search.semantic_similarity_weight, loader.config.storage.duckdb_path)
    )
    Orchestrator.run_query("q", loader.config)
    cfg_file.write_text(
        tomli_w.dumps(
            {
                "agents": ["AgentA"],
                "search": {
                    "backends": ["b1"],
                    "context_aware": {"enabled": False},
                    "semantic_similarity_weight": 0.2,
                    "bm25_weight": 0.7,
                    "source_credibility_weight": 0.1,
                },
                "storage": {"duckdb_path": "db2.duckdb"},
            }
        )
    )
    repo.index.add([str(cfg_file)])
    repo.index.commit("update config")
    time.sleep(0.2)
    Orchestrator.run_query("q", loader.config)
    loader.stop_watching()

    assert weights == [(0.7, 0.2, 0.1), (0.2, 0.7, 0.1)]
    assert paths == ["db1.duckdb", "db2.duckdb"]
    assert events[0] == (0.7, "db1.duckdb") and events[-1] == (0.2, "db2.duckdb")
