import time
import tomllib
from contextlib import contextmanager

import git
import pytest
import tomli_w

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import orchestrator as orch_mod
from tests.conftest import GITPYTHON_INSTALLED

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory
StorageManager = orch_mod.StorageManager


class Search:
    backends: dict[str, callable] = {}

    @staticmethod
    def external_lookup(query: str, max_results: int = 5):  # pragma: no cover - stub
        results = []
        for backend in Search.backends.values():
            results.extend(backend(query, max_results))
        return results


pytestmark = [
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
            StorageManager.persist_claim(
                {"id": self.name, "type": "fact", "content": self.name}
            )
            calls.append(self.name)
            state.update(
                {
                    "results": {self.name: "ok"},
                    "claims": [{"id": self.name, "type": "fact", "content": self.name}],
                }
            )
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {"results": {self.name: "ok"}}

    return DummyAgent(name)


def test_config_hot_reload(tmp_path, monkeypatch):
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
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: stored.append(claim["id"])
    )
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
    assert stored == ["AgentA", "AgentB"]
    assert search_calls == ["b1", "b2"]
    assert events[0] == (["AgentA"], ["b1"]) and events[-1] == (["AgentB"], ["b2"])
