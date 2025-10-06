# mypy: ignore-errors
import json
import sys
import types
from pathlib import Path

import pytest
from autoresearch.orchestration import metrics


@pytest.mark.unit
def test_metrics_reset_and_temporary(monkeypatch: pytest.MonkeyPatch) -> None:

    class DummyHist:
        def __init__(self) -> None:
            self._sum = types.SimpleNamespace(get=lambda: 0, set=lambda v: None)
            self._count = types.SimpleNamespace(get=lambda: 0, set=lambda v: None)

        def observe(self, v: float) -> None:  # pragma: no cover - stub
            pass

    monkeypatch.setattr(metrics, "KUZU_QUERY_TIME", DummyHist())
    metrics.QUERY_COUNTER.inc(3)
    with metrics.temporary_metrics():
        metrics.QUERY_COUNTER.inc(2)
        assert metrics.QUERY_COUNTER._value.get() == 5
    assert metrics.QUERY_COUNTER._value.get() == 3
    metrics.reset_metrics()
    assert metrics.QUERY_COUNTER._value.get() == 0


@pytest.mark.unit
def test_get_system_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyProcess:
        def memory_info(self) -> types.SimpleNamespace:
            return types.SimpleNamespace(rss=50 * 1024 * 1024)

    dummy_psutil = types.SimpleNamespace(
        cpu_percent=lambda interval=None: 10.0,
        Process=lambda: DummyProcess(),
    )
    dummy_nvml = types.SimpleNamespace(
        nvmlInit=lambda: None,
        nvmlDeviceGetCount=lambda: 1,
        nvmlShutdown=lambda: None,
        nvmlDeviceGetHandleByIndex=lambda idx: 0,
        nvmlDeviceGetUtilizationRates=lambda handle: types.SimpleNamespace(gpu=20),
        nvmlDeviceGetMemoryInfo=lambda handle: types.SimpleNamespace(used=30 * 1024 * 1024),
    )
    monkeypatch.setitem(sys.modules, "psutil", dummy_psutil)
    monkeypatch.setitem(sys.modules, "pynvml", dummy_nvml)
    cpu, mem, gpu, gpu_mem = metrics._get_system_usage()
    assert (cpu, mem, gpu, gpu_mem) == (10.0, 50.0, 20.0, 30.0)


@pytest.mark.unit
def test_token_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(tmp_path / "rel.json"))
    metrics.reset_metrics()
    m = metrics.OrchestrationMetrics()
    m.record_tokens("a", 2, 3)
    m.start_cycle()
    m.end_cycle()
    path = tmp_path / "q.json"
    m.record_query_tokens("q", path)
    assert json.loads(path.read_text()) == {"q": 5}
    baseline = tmp_path / "base.json"
    baseline.write_text(json.dumps({"q": 4}))
    assert m.check_query_regression("q", baseline)
    monkeypatch.setitem(
        sys.modules,
        "autoresearch.llm.token_counting",
        types.SimpleNamespace(compress_prompt=lambda p, b: "short"),
    )
    long_prompt = "word " * 50
    assert m.compress_prompt_if_needed(long_prompt, 20) == "short"
    m.record_tokens("a", 1, 0)
    assert m.suggest_token_budget(10) >= 1
