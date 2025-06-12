from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.llm import DummyAdapter
import autoresearch.llm as llm


def test_capture_token_usage(monkeypatch):
    m = OrchestrationMetrics()
    monkeypatch.setattr(llm, "get_llm_adapter", lambda name: DummyAdapter())
    with Orchestrator._capture_token_usage("agent", m):
        adapter = llm.get_llm_adapter("dummy")
        adapter.generate("hello world")
    counts = m.token_counts["agent"]
    assert counts["in"] == 2
    assert counts["out"] > 0
