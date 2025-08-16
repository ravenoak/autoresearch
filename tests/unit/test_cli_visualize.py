import importlib
from unittest.mock import MagicMock

from typer.testing import CliRunner

from autoresearch.cli_utils import ascii_bar_graph, summary_table
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def test_ascii_bar_graph_basic():
    graph = ascii_bar_graph({"a": 1, "b": 2}, width=10)
    lines = graph.splitlines()
    assert len(lines) == 2
    assert lines[0].count("#") < lines[1].count("#")


def test_summary_table_render():
    table = summary_table({"x": 1})
    from rich.console import Console

    console = Console(record=True, color_system=None)
    console.print(table)
    output = console.export_text()
    assert "x" in output
    assert "1" in output


def test_search_visualize_option(dummy_storage, monkeypatch):
    runner = CliRunner()

    orch = Orchestrator()
    run_query_mock = MagicMock(
        return_value=QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={"m": 1}
        )
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
