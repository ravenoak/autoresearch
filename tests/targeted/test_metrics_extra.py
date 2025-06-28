import types
import pytest
from autoresearch.orchestration import metrics


def test_cycle_and_agent_metrics(monkeypatch):
    fake_time = types.SimpleNamespace(time=lambda: 1.0)
    monkeypatch.setattr(metrics, "time", fake_time)
    m = metrics.OrchestrationMetrics()
    m.start_cycle()
    m.record_agent_timing("agent", 0.5)
    m.record_tokens("agent", 2, 3)
    m.record_error("agent")
    m.end_cycle()
    summary = m.get_summary()
    assert summary["cycles_completed"] == 1
    assert summary["agent_timings"]["agent"] == [0.5]
    assert summary["agent_tokens"]["agent"]["in"] == 2
    assert summary["agent_tokens"]["agent"]["out"] == 3
    assert summary["errors"]["total"] == 1
