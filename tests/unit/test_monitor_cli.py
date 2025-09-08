from typing import Any, Dict, List

import psutil  # type: ignore
from typer.testing import CliRunner
import typer

try:
    import docx  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    import tests.stubs.docx  # noqa: F401

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.main import app
from autoresearch.models import QueryResponse
from autoresearch.orchestration import metrics as orch_metrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.search import Search


def assert_bm25_signature(query: str, documents: List[Dict[str, Any]]) -> List[float]:
    """Stub ensuring BM25 receives ``(query, documents)``."""
    assert isinstance(query, str)
    assert isinstance(documents, list)
    return [1.0] * len(documents)


def dummy_run_query(query, config, callbacks=None, **kwargs):
    assert callbacks is not None and "on_cycle_end" in callbacks
    # Exercise BM25 scoring to verify call signature
    Search.calculate_bm25_scores(query=query, documents=[{"title": "t", "url": "u"}])
    dummy_state = type(
        "S",
        (),
        {
            "metadata": {"execution_metrics": {}},
            "claims": [],
            "error_count": 0,
        },
    )()
    callbacks["on_cycle_end"](0, dummy_state)
    return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})


def test_monitor_prompts_and_passes_callbacks(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: ConfigModel(
            loops=1,
            output_format="json",
            storage=StorageConfig(vector_extension=False),
        ),
    )
    responses = iter(["test", "", "q"])
    monkeypatch.setattr(typer, "prompt", lambda *a, **k: next(responses))
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(assert_bm25_signature))
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    result = runner.invoke(app, ["monitor", "run"])
    assert result.exit_code == 0


def test_monitor_metrics(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: type("C", (), {})())
    orch_metrics.reset_metrics()
    orch_metrics.QUERY_COUNTER._value.set(5)
    orch_metrics.TOKENS_IN_COUNTER._value.set(7)
    orch_metrics.TOKENS_OUT_COUNTER._value.set(9)

    class Mem:
        percent = 2.0
        used = 2 * 1024 * 1024

    class Proc:
        def memory_info(self):
            return type("I", (), {"rss": 3 * 1024 * 1024})()

    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 1.0)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: Mem)
    monkeypatch.setattr(psutil, "Process", lambda: Proc())
    monkeypatch.setattr("autoresearch.resource_monitor._get_gpu_stats", lambda: (4.0, 5.0))

    result = runner.invoke(app, ["monitor", "metrics"])
    assert result.exit_code == 0
    out = result.stdout
    assert "cpu_percent" in out and "1.0" in out
    assert "memory_percent" in out and "2.0" in out
    assert "memory_used_mb" in out and "2.0" in out
    assert "process_memory_mb" in out and "3.0" in out
    assert "gpu_percent" in out and "4.0" in out
    assert "gpu_memory_mb" in out and "5.0" in out
    assert "queries_total" in out and "5" in out
    assert "tokens_in_total" in out and "7" in out
    assert "tokens_out_total" in out and "9" in out


def test_monitor_metrics_default_counters(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: type("C", (), {})())
    orch_metrics.reset_metrics()

    class Mem:
        percent = 2.0
        used = 2 * 1024 * 1024

    class Proc:
        def memory_info(self):
            return type("I", (), {"rss": 3 * 1024 * 1024})()

    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 1.0)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: Mem)
    monkeypatch.setattr(psutil, "Process", lambda: Proc())
    monkeypatch.setattr("autoresearch.resource_monitor._get_gpu_stats", lambda: (4.0, 5.0))

    result = runner.invoke(app, ["monitor", "metrics"])
    assert result.exit_code == 0
    out = result.stdout
    assert "queries_total" in out and "0" in out
    assert "tokens_in_total" in out and "0" in out
    assert "tokens_out_total" in out and "0" in out
