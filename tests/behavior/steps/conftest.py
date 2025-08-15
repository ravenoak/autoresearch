import pytest

from autoresearch.orchestration.orchestrator import Orchestrator


@pytest.fixture(autouse=True)
def orchestrator_runner(monkeypatch):
    """Ensure step definitions use a fresh Orchestrator per invocation."""
    orig_run_query = Orchestrator.run_query

    def run_query_wrapper(query, config, callbacks=None, **kwargs):
        return orig_run_query(Orchestrator(), query, config, callbacks, **kwargs)

    monkeypatch.setattr(Orchestrator, "run_query", staticmethod(run_query_wrapper))
    monkeypatch.setattr(Orchestrator, "_orig_run_query", orig_run_query, raising=False)
