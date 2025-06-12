from typer.testing import CliRunner
from autoresearch.main import app
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _mock_run_query(query, config):
    return QueryResponse(answer="a", citations=[], reasoning=[], metrics={})


def test_search_default_output_tty(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    result = runner.invoke(app, ["search", "q"])
    assert result.exit_code == 0
    assert "# Answer" in result.stdout


def test_search_default_output_json(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = runner.invoke(app, ["search", "q"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("{")


def test_config_command(monkeypatch):
    runner = CliRunner()

    class Cfg:
        def json(self, indent=2):
            return "{\n  \"loops\": 1\n}"

    monkeypatch.setattr(
        "autoresearch.main._config_loader.load_config",
        lambda: Cfg(),
    )
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert '"loops"' in result.stdout
