import json
from typing import Any, Dict, List

import psutil  # type: ignore
from typer.testing import CliRunner

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
    monkeypatch.setattr(
        "autoresearch.main.Prompt.ask",
        lambda *a, **k: next(responses),
    )
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

    result = runner.invoke(app, ["monitor"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["cpu_percent"] == 1.0
    assert data["memory_percent"] == 2.0
    assert data["memory_used_mb"] == 2.0
    assert data["process_memory_mb"] == 3.0
    assert data["gpu_percent"] == 4.0
    assert data["gpu_memory_mb"] == 5.0
    assert data["queries_total"] == 5
    assert data["tokens_in_total"] == 7
    assert data["tokens_out_total"] == 9


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

    result = runner.invoke(app, ["monitor"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["queries_total"] == 0
    assert data["tokens_in_total"] == 0
    assert data["tokens_out_total"] == 0
