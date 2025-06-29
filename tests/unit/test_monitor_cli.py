from typer.testing import CliRunner
from autoresearch.main import app
from autoresearch.config import ConfigLoader, ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def dummy_run_query(query, config, callbacks=None, **kwargs):
    assert callbacks is not None and "on_cycle_end" in callbacks
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
        lambda self: ConfigModel(loops=1, output_format="json"),
    )
    responses = iter(["test", "", "q"])
    monkeypatch.setattr(
        "autoresearch.main.Prompt.ask",
        lambda *a, **k: next(responses),
    )
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    result = runner.invoke(app, ["monitor", "run"])
    assert result.exit_code == 0


def test_monitor_metrics(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics", lambda: {"cpu_percent": 1.0, "memory_percent": 2.0}
    )
    result = runner.invoke(app, ["monitor"])
    assert result.exit_code == 0
    assert "cpu_percent" in result.stdout
