from typer.testing import CliRunner
from fastapi.testclient import TestClient

from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration.orchestrator import (
    Orchestrator,
    AgentFactory,
)
from autoresearch.llm import DummyAdapter


class DummyStorage:
    persisted = []

    @staticmethod
    def persist_claim(claim):
        DummyStorage.persisted.append(claim)


def _patch_run_query(monkeypatch):
    original = Orchestrator.run_query

    def wrapper(query, config, callbacks=None, **kwargs):
        return original(
            query,
            config,
            callbacks,
            agent_factory=AgentFactory,
            storage_manager=DummyStorage,
        )

    monkeypatch.setattr(Orchestrator, "run_query", wrapper)


def _common_patches(monkeypatch):
    cfg = ConfigModel(loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        "autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter()
    )
    monkeypatch.setattr(
        "autoresearch.agents.dialectical.synthesizer.get_llm_adapter",
        lambda name: DummyAdapter(),
    )
    monkeypatch.setattr(
        "autoresearch.agents.dialectical.contrarian.get_llm_adapter",
        lambda name: DummyAdapter(),
    )
    monkeypatch.setattr(
        "autoresearch.agents.dialectical.fact_checker.get_llm_adapter",
        lambda name: DummyAdapter(),
    )
    monkeypatch.setattr(
        "autoresearch.search.Search.external_lookup",
        lambda q, max_results=5: [{"title": "t", "url": "u"}],
    )
    _patch_run_query(monkeypatch)


def test_cli_flow(monkeypatch):
    _common_patches(monkeypatch)
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = runner.invoke(
        cli_app, ["search", "test query", "--output", "markdown"]
    )
    assert result.exit_code == 0
    assert "# Answer" in result.stdout
    assert DummyStorage.persisted


def test_http_flow(monkeypatch):
    _common_patches(monkeypatch)
    client = TestClient(api_app)
    resp = client.post("/query", json={"query": "test query"})
    assert resp.status_code == 200
    data = resp.json()
    for key in ["answer", "citations", "reasoning", "metrics"]:
        assert key in data
    assert DummyStorage.persisted


def test_http_no_query_field(monkeypatch):
    _common_patches(monkeypatch)
    client = TestClient(api_app)
    resp = client.post("/query", json={})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "`query` field is required"
