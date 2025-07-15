from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def _setup(monkeypatch):
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel(loops=1))

    def dummy_run_query(query, config, callbacks=None, **kwargs):
        return QueryResponse(
            answer="ok",
            citations=["c"],
            reasoning=["r"],
            metrics={"m": 1},
        )

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)


def test_search_visualize_option_integration(monkeypatch):
    _setup(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "q", "--visualize"])
    assert result.exit_code == 0
    assert "Knowledge Graph" in result.stdout
    assert "m" in result.stdout


def test_visualize_command_integration(monkeypatch, tmp_path):
    _setup(monkeypatch)
    saved = {}

    def fake_save(result, path, layout="spring"):
        saved["path"] = str(path)

    monkeypatch.setattr("autoresearch.visualization.save_knowledge_graph", fake_save)
    runner = CliRunner()
    out_file = tmp_path / "graph.png"
    result = runner.invoke(cli_app, ["visualize", "q", str(out_file)])
    assert result.exit_code == 0
    assert saved.get("path") == str(out_file)
    assert "Graph written" in result.stdout
    assert "Metrics Summary" in result.stdout
