from typing import Any, Dict, List

from typer.testing import CliRunner

try:
    import docx  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    import tests.stubs.docx  # noqa: F401

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.main import app
from autoresearch.models import QueryResponse
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
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 1.0, "memory_percent": 2.0},
    )
    result = runner.invoke(app, ["monitor"])
    assert result.exit_code == 0
    assert "cpu_percent" in result.stdout
