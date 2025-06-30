import importlib
from typer.testing import CliRunner

from autoresearch.cli_utils import ascii_bar_graph, summary_table
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def test_ascii_bar_graph_basic():
    graph = ascii_bar_graph({'a': 1, 'b': 2}, width=10)
    lines = graph.splitlines()
    assert len(lines) == 2
    assert lines[0].count('#') < lines[1].count('#')


def test_summary_table_render():
    table = summary_table({'x': 1})
    from rich.console import Console
    console = Console(record=True, color_system=None)
    console.print(table)
    output = console.export_text()
    assert 'x' in output
    assert '1' in output


def test_search_visualize_option(monkeypatch):
    runner = CliRunner()

    def _mock_run(query, config, callbacks=None):
        return QueryResponse(answer='a', citations=[], reasoning=[], metrics={'m': 1})

    monkeypatch.setattr(Orchestrator, 'run_query', _mock_run)
    from autoresearch.config import ConfigLoader, ConfigModel
    monkeypatch.setattr(ConfigLoader, 'load_config', lambda self: ConfigModel(loops=1))
    main = importlib.import_module('autoresearch.main')
    result = runner.invoke(main.app, ['search', 'q', '--visualize'])
    assert result.exit_code == 0
    assert 'Knowledge Graph' in result.stdout
    assert 'm' in result.stdout
    assert 'Answer' in result.stdout
