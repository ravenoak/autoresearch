# flake8: noqa
import os
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
from autoresearch import cache, tracing


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


@pytest.fixture(autouse=True)
def reset_tinydb_and_metrics(tmp_path, monkeypatch):
    """Use temporary cache and metrics files for each scenario."""
    original_env = {
        "TINYDB_PATH": os.environ.get("TINYDB_PATH"),
        "AUTORESEARCH_RELEASE_METRICS": os.environ.get(
            "AUTORESEARCH_RELEASE_METRICS"
        ),
        "AUTORESEARCH_QUERY_TOKENS": os.environ.get("AUTORESEARCH_QUERY_TOKENS"),
    }
    db_path = tmp_path / "cache.json"
    monkeypatch.setenv("TINYDB_PATH", str(db_path))
    cache.teardown(remove_file=True)
    cache.setup(str(db_path))
    release = tmp_path / "release_tokens.json"
    query = tmp_path / "query_tokens.json"
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(release))
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", str(query))
    yield
    cache.teardown(remove_file=True)
    for env_var, value in original_env.items():
        if value is None:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = value
    for path in (release, query):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.fixture(autouse=True)
def reset_tracer_provider():
    """Ensure tracer provider does not leak between scenarios."""
    original_provider = tracing._tracer_provider
    tracing._tracer_provider = None
    yield
    if tracing._tracer_provider:
        tracing._tracer_provider.shutdown()
    tracing._tracer_provider = original_provider


@pytest.fixture
def mock_llm_adapter(monkeypatch):
    """Use a DummyAdapter to avoid external LLM calls.

    This fixture isolates LLM interactions so each scenario runs with a
    predictable, in-memory adapter that performs no network requests.
    """
    from autoresearch.llm import DummyAdapter

    monkeypatch.setattr(
        "autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter()
    )
    yield


@pytest.fixture
def temp_config(tmp_path, monkeypatch, mock_llm_adapter):
    """Create an isolated configuration file for each scenario.

    The working directory is changed to a temporary location and a minimal
    `autoresearch.toml` is written. Any state is discarded after the test
    completes, preventing leakage between scenarios.
    """
    monkeypatch.chdir(tmp_path)
    cfg = {
        "core": {"backend": "lmstudio", "loops": 1, "ram_budget_mb": 512},
        "search": {"backends": [], "context_aware": {"enabled": False}},
    }
    with open("autoresearch.toml", "w") as f:
        import tomli_w

        f.write(tomli_w.dumps(cfg))
    return tmp_path / "autoresearch.toml"


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
def application_running(temp_config):
    """Ensure the application runs with isolated config and mocked LLM."""
    return


@given("the application is running with default configuration")
def app_running_with_default(temp_config):
    return application_running(temp_config)


@given("the application is running")
def app_running(temp_config):
    return application_running(temp_config)
