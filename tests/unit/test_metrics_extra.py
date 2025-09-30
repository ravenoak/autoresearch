from autoresearch.orchestration import metrics
import pytest
from pathlib import Path


def test_cycle_and_agent_metrics(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_time() -> float:
        return 1.0

    monkeypatch.setattr(metrics.time, "time", fake_time)
    assert callable(metrics.time.time)
    path = tmp_path / "dir" / "release.json"
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(path))
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
    if path.exists():
        path.unlink()


def test_resource_tracking(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        metrics,
        "_get_system_usage",
        lambda: (50.0, 100.0, 25.0, 512.0),
    )
    m = metrics.OrchestrationMetrics()
    m.record_system_resources()
    rec = m.get_summary()["resource_usage"][0]
    assert rec["cpu_percent"] == 50.0
    assert rec["memory_mb"] == 100.0
    assert rec["gpu_percent"] == 25.0
    assert rec["gpu_memory_mb"] == 512.0
