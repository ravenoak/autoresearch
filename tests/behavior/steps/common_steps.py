# flake8: noqa
import pytest
from pytest_bdd import given

from autoresearch.main import app as cli_app
from autoresearch.agents.registry import AgentRegistry
from autoresearch.storage import (
    StorageManager,
    set_delegate as set_storage_delegate,
    setup as storage_setup,
    teardown as storage_teardown,
)
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


@pytest.fixture(autouse=True)
def reset_global_registries(tmp_path):
    """Reset global Agent and Storage registries before each scenario."""
    AgentRegistry._registry.clear()
    AgentRegistry._coalitions.clear()
    db_file = tmp_path / "kg.duckdb"
    storage_teardown(remove_db=True)
    storage_setup(str(db_file))
    set_storage_delegate(StorageManager)
    StorageManager._access_frequency.clear()
    StorageManager._last_adaptive_policy = "lru"
    yield
    AgentRegistry._registry.clear()
    AgentRegistry._coalitions.clear()
    StorageManager._access_frequency.clear()
    StorageManager._last_adaptive_policy = "lru"
    storage_teardown(remove_db=True)


@pytest.fixture
def dummy_query_response(monkeypatch):
    """Provide a deterministic orchestrator result for interface tests."""
    response = QueryResponse(
        answer="test answer",
        citations=["source"],
        reasoning=["step"],
        metrics={
            "time_ms": 1,
            "tokens": 1,
            "agent_sequence": ["Synthesizer", "Contrarian"],
        },
    )
    monkeypatch.setattr(
        Orchestrator, "run_query", lambda *a, **k: response
    )
    return response


@given("the Autoresearch application is running")
def application_running(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {
        "core": {"backend": "lmstudio", "loops": 1, "ram_budget_mb": 512},
        "search": {"backends": [], "context_aware": {"enabled": False}},
    }
    with open("autoresearch.toml", "w") as f:
        import tomli_w

        f.write(tomli_w.dumps(cfg))

    from autoresearch.llm import DummyAdapter

    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())
    return


@given("the application is running with default configuration")
def app_running_with_default(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)


@given("the application is running")
def app_running(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)
