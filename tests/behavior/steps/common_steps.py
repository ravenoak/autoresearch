# flake8: noqa
import os
import shlex

import pytest
from pytest_bdd import given, parsers, then, when

from autoresearch import cache, tracing
from autoresearch.agents.registry import AgentRegistry
from autoresearch.errors import TimeoutError
from autoresearch.main import app as cli_app
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.storage import (
    StorageManager,
)
from autoresearch.storage import set_delegate as set_storage_delegate
from autoresearch.storage import setup as storage_setup
from autoresearch.storage import teardown as storage_teardown


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
        "AUTORESEARCH_RELEASE_METRICS": os.environ.get("AUTORESEARCH_RELEASE_METRICS"),
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

    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())
    yield


@pytest.fixture
def dummy_query_response(monkeypatch):
    """Provide a deterministic orchestrator result for interface tests."""
    response = QueryResponse(
        query="test query",
        answer="test answer",
        citations=["source"],
        reasoning=["step"],
        metrics={
            "time_ms": 1,
            "tokens": 1,
            "agent_sequence": ["Synthesizer", "Contrarian"],
        },
    )
    monkeypatch.setattr(Orchestrator, "run_query", lambda *a, **k: response)
    return response


@pytest.fixture
def isolate_network(monkeypatch):
    """Block outbound network requests for the duration of a test."""

    def _deny(*args, **kwargs):  # pragma: no cover - simple guard
        raise RuntimeError("Network access disabled during tests")

    try:  # requests might not be installed
        import requests

        monkeypatch.setattr(requests.sessions.Session, "request", _deny)
    except Exception:  # pragma: no cover - safety
        pass

    try:  # httpx is optional
        import httpx

        monkeypatch.setattr(httpx.Client, "request", _deny, raising=False)
    except Exception:  # pragma: no cover - safety
        pass

    yield


@pytest.fixture
def restore_environment():
    """Snapshot ``os.environ`` and restore it after the test."""

    original = os.environ.copy()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


def assert_cli_success(result):
    """Assert that a CLI invocation succeeded without errors."""
    assert result.exit_code == 0, result.stderr
    assert result.stdout != ""
    assert result.stderr == ""


def assert_cli_error(result):
    """Assert that a CLI invocation failed and produced an error message."""
    assert result.exit_code != 0
    assert result.stderr != "" or result.exception is not None


@pytest.fixture
def orchestrator_failure(monkeypatch):
    """Simulate orchestrator-level failures for targeted scenarios."""

    def _simulate(kind: str | None = None):
        if kind == "timeout":

            def _timeout(*_a, **_k):
                raise TimeoutError("simulated orchestrator timeout")

            monkeypatch.setattr(Orchestrator, "run_query", _timeout)
        elif kind == "metrics":

            def _metrics(*_a, **_k):
                return QueryResponse(
                    answer="",
                    citations=[],
                    reasoning=[],
                    metrics=None,
                )

            monkeypatch.setattr(Orchestrator, "run_query", _metrics)

    return _simulate


@given(parsers.re("the (?:Autoresearch )?application is running(?: with default configuration)?"))
def application_running(temp_config):
    """Ensure the application runs with isolated config and mocked LLM."""
    return


# Shared CLI step implementations
@when(parsers.parse("I run `{command}`"))
def run_cli_command(cli_runner, bdd_context, command, isolate_network, restore_environment):
    args = shlex.split(command)
    if args and args[0] == "autoresearch":
        args = args[1:]
    result = cli_runner.invoke(cli_app, args, catch_exceptions=False)
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_should_exit_successfully(bdd_context):
    assert_cli_success(bdd_context["result"])


@then("the CLI should report an error")
def cli_should_report_error(bdd_context):
    assert_cli_error(bdd_context["result"])


# Backward-compatible aliases for legacy imports
app_running = application_running
app_running_with_default = application_running
