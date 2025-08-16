import builtins
import sys
import types
from unittest.mock import MagicMock

import pytest


from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import parallel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.errors import AgentError, OrchestrationError


def test_get_memory_usage_fallback(monkeypatch):
    if "psutil" in sys.modules:
        del sys.modules["psutil"]

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    fake_resource = types.SimpleNamespace(
        getrusage=lambda *a, **k: types.SimpleNamespace(ru_maxrss=2048),
        RUSAGE_SELF=0,
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)
    assert parallel._get_memory_usage() == 2.0


def test_calculate_result_confidence():
    resp = QueryResponse(
        answer="a",
        citations=["c1", "c2"],
        reasoning=["r"] * 5,
        metrics={"token_usage": {"total": 50, "max_tokens": 100}, "errors": []},
    )
    score = parallel._calculate_result_confidence(resp)
    assert 0.5 <= score <= 1.0


def test_execute_parallel_query_basic(monkeypatch):
    cfg = ConfigModel.model_construct(agents=[], loops=1)

    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def set_attribute(self, *args, **kwargs):
            pass

        def add_event(self, *args, **kwargs):
            pass

    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()

    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.get_tracer",
        lambda name: DummyTracer(),
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.setup_tracing", lambda enabled: None
    )

    def run_query_stub(
        query,
        config,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
    ):
        return QueryResponse(
            answer=config.agents[0],
            citations=[],
            reasoning=[config.agents[0]],
            metrics={"token_usage": {"total": 10, "max_tokens": 100}, "errors": []},
        )

    orc1 = Orchestrator()
    orc2 = Orchestrator()
    mock1 = MagicMock(side_effect=run_query_stub)
    mock2 = MagicMock(side_effect=run_query_stub)
    monkeypatch.setattr(orc1, "run_query", mock1)
    monkeypatch.setattr(orc2, "run_query", mock2)

    orchestrators = [orc1, orc2]

    class DummyOrchestrator:
        def __init__(self):
            self.inst = orchestrators.pop(0)

        def run_query(self, *args, **kwargs):
            return self.inst.run_query(*args, **kwargs)

    synthesizer = MagicMock()
    synthesizer.execute.return_value = {"answer": "final"}

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator",
        DummyOrchestrator,
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: synthesizer,
    )

    resp = parallel.execute_parallel_query("q", cfg, [["A"], ["B"]])

    assert isinstance(resp, QueryResponse)
    assert resp.answer == "final"
    assert resp.metrics["parallel_execution"]["successful_groups"] == 2
    assert mock1.called and mock2.called


def test_execute_parallel_query_agent_error(monkeypatch, caplog):
    cfg = ConfigModel.model_construct(agents=[], loops=1)

    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def set_attribute(self, *args, **kwargs):
            pass

        def add_event(self, *args, **kwargs):
            pass

    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()

    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.get_tracer",
        lambda name: DummyTracer(),
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.setup_tracing", lambda enabled: None
    )

    def run_query_error(
        query,
        config,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
    ):
        raise AgentError("boom", agent_name="A")

    orc = Orchestrator()
    mock_run = MagicMock(side_effect=run_query_error)
    monkeypatch.setattr(orc, "run_query", mock_run)

    class DummyOrchestrator:
        def __init__(self):
            self.inst = orc

        def run_query(self, *args, **kwargs):
            return self.inst.run_query(*args, **kwargs)

    synthesizer = MagicMock()
    synthesizer.execute.return_value = {"answer": "final"}

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator",
        DummyOrchestrator,
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: synthesizer,
    )

    with caplog.at_level("ERROR"):
        with pytest.raises(OrchestrationError):
            parallel.execute_parallel_query("q", cfg, [["A"]])

    assert mock_run.called
