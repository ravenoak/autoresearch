import time
import tomli_w
import tomllib
from types import SimpleNamespace
from contextlib import contextmanager

from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.search import Search
from autoresearch.storage import StorageManager


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


def test_config_hot_reload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_file = tmp_path / "autoresearch.toml"
    cfg_file.write_text(
        tomli_w.dumps(
            {
                "agents": ["AgentA"],
                "search": {"backends": ["b1"], "context_aware": {"enabled": False}},
            }
        )
    )
    ConfigLoader.reset_instance()

    def fake_load(self):
        data = tomllib.loads(cfg_file.read_text())
        return SimpleNamespace(
            agents=data["agents"],
            loops=1,
            search=SimpleNamespace(
                backends=data["search"]["backends"],
                context_aware=SimpleNamespace(enabled=False),
            ),
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
        return results

    monkeypatch.setattr(Search, "external_lookup", external_lookup)

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(
        Orchestrator, "_capture_token_usage", no_token_capture
    )

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
        time.sleep(0.1)
        Orchestrator.run_query("q", loader.config)

    assert calls == ["AgentA", "AgentB"]
    assert stored == ["AgentA", "AgentB"]
    assert search_calls == ["b1", "b2"]
    assert events[0] == (["AgentA"], ["b1"]) and events[-1] == (["AgentB"], ["b2"])
