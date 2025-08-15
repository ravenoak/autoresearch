import pytest

from autoresearch.orchestration.orchestrator import Orchestrator


@pytest.fixture(autouse=True)
def orchestrator_runner(monkeypatch):
    """Ensure step definitions use a fresh Orchestrator per invocation."""
    orig_run_query = Orchestrator.run_query
    orig_run_query_async = Orchestrator.run_query_async

    def run_query_wrapper(query, config, callbacks=None, **kwargs):
        return orig_run_query(Orchestrator(), query, config, callbacks, **kwargs)

    async def run_query_async_wrapper(query, config, callbacks=None, **kwargs):
        return await orig_run_query_async(
            Orchestrator(), query, config, callbacks, **kwargs
        )

    monkeypatch.setattr(Orchestrator, "run_query", staticmethod(run_query_wrapper))
    monkeypatch.setattr(
        Orchestrator,
        "run_query_async",
        staticmethod(run_query_async_wrapper),
    )
    monkeypatch.setattr(Orchestrator, "_orig_run_query", orig_run_query, raising=False)
    monkeypatch.setattr(
        Orchestrator, "_orig_run_query_async", orig_run_query_async, raising=False
    )
