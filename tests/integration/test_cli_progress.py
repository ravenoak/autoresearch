from typing import Any

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

    def capture_prompt(*_args, **kwargs):
        prompts.append(kwargs.get("default", ""))
        return ""

    monkeypatch.setattr("autoresearch.main.Prompt.ask", capture_prompt)

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


def test_cli_search_uses_model_copy(monkeypatch, tmp_path):
    """The search command should clone configs via ``model_copy`` when updating."""

    import autoresearch.main as main_module

    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 1\n", encoding="utf-8")

    monkeypatch.setattr(main_module._config_loader, "search_paths", [config_path])
    monkeypatch.setattr(main_module._config_loader, "env_path", tmp_path / ".env")

    cfg = ConfigModel()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(main_module._config_loader, "_config", cfg)

    copy_calls: list[dict[str, Any]] = []
    original_model_copy = ConfigModel.model_copy

    def _spy_model_copy(
        self: ConfigModel,
        *,
        update: dict[str, Any] | None = None,
        deep: bool = False,
    ) -> ConfigModel:
        copy_calls.append({"update": update, "deep": deep})
        return original_model_copy(self, update=update, deep=deep)

    monkeypatch.setattr(ConfigModel, "model_copy", _spy_model_copy)

    class StubStorageManager:
        @staticmethod
        def setup() -> None:  # pragma: no cover - no side effects in tests
            return None

    monkeypatch.setattr("autoresearch.storage.StorageManager", StubStorageManager)

    def dummy_run_query(self, query, config, callbacks=None, visualize=None, **kwargs):
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator.run_query",
        dummy_run_query,
    )
    monkeypatch.setattr("autoresearch.output_format.OutputFormatter.format", lambda *_, **__: None)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "prompt", "--loops", "3"])

    assert result.exit_code == 0
    assert copy_calls, "Expected ConfigModel.model_copy to be invoked"
    assert copy_calls[0]["update"] == {"loops": 3}
