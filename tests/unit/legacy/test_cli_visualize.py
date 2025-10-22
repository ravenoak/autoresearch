# mypy: ignore-errors
import importlib
from unittest.mock import MagicMock

from typer.testing import CliRunner

from autoresearch.cli_utils import (
    get_console,
    render_metrics_panel,
    set_bare_mode,
    summary_table,
)
from autoresearch.models import QueryResponse
import pytest


pytestmark = pytest.mark.usefixtures("dummy_storage")


def test_render_metrics_panel_bare_mode(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_BARE_MODE", "1")
    set_bare_mode(True)
    try:
        renderable = render_metrics_panel({"a": 1, "b": 2})
        assert isinstance(renderable, str)
        assert "a" in renderable
        assert "#" in renderable
    finally:
        monkeypatch.delenv("AUTORESEARCH_BARE_MODE", raising=False)
        set_bare_mode(False)


def test_summary_table_render():
    table = summary_table({"x": 1})
    console = get_console(force_refresh=True)
    with console.capture() as capture:
        console.print(table)
    output = capture.get()
    assert "x" in output
    assert "1" in output


def test_search_visualize_option(monkeypatch, dummy_storage, orchestrator):
    runner = CliRunner()

    orch = orchestrator
    run_query_mock = MagicMock(
        return_value=QueryResponse(answer="ok", citations=[], reasoning=[], metrics={"m": 1})
    )
    monkeypatch.setattr(orch, "run_query", run_query_mock)

    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main_app = importlib.import_module("autoresearch.main.app")
    monkeypatch.setattr(main_app, "Orchestrator", lambda: orch)
    main = importlib.import_module("autoresearch.main")
    result = runner.invoke(main.app, ["search", "q", "--visualize"])
    assert result.exit_code == 0
    run_query_mock.assert_called_once()
    assert run_query_mock.call_args.kwargs["visualize"] is True
    assert "Knowledge Graph" in result.stdout
    assert "m" in result.stdout
    assert "Answer" in result.stdout
