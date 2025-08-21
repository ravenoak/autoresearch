from autoresearch.main import app as cli_app
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState
from typer.testing import CliRunner


class DummyProgress:
    def __init__(self):
        self.updates = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def add_task(self, *args, **kwargs):
        return 0

    def update(self, *args, **kwargs):
        self.updates.append(kwargs.get("advance", 0))


def test_cli_progress_and_interactive(monkeypatch):
    progress_instances = []

    def progress_factory(*args, **kwargs):
        p = DummyProgress()
        progress_instances.append(p)
        return p

    cfg = ConfigModel(loops=2)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    # Patch Progress and Prompt via the package to intercept runtime imports
    monkeypatch.setattr("autoresearch.main.Progress", progress_factory)

    prompts = []
    monkeypatch.setattr(
        "autoresearch.main.Prompt.ask",
        lambda *a, **k: prompts.append(k.get("default", "")) or "",
    )

    def dummy_run_query(self, query, config, callbacks=None, **kwargs):
        state = QueryState(query=query)
        for i in range(config.loops):
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](i, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test", "--interactive"])
    assert result.exit_code == 0
    assert progress_instances[0].updates == [1, 1]
    # One prompt for each cycle except the last
    assert len(prompts) == 1
