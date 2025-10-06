# mypy: ignore-errors
import importlib
from pathlib import Path

from typer.testing import CliRunner


def test_cli_help_no_ansi(monkeypatch, dummy_storage):
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["--help"])
    assert result.exit_code == 0
    assert "\x1b[" not in result.stdout
    assert "Usage:" in result.stdout


def test_search_help_includes_interactive(monkeypatch, dummy_storage):
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--interactive" in result.stdout
    assert "--loops" in result.stdout


def test_search_help_includes_visualize(monkeypatch, dummy_storage):
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--visualize" in result.stdout


def test_search_loops_option(monkeypatch, dummy_storage):
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel
    from autoresearch.models import QueryResponse

    loaded = {}

    def _load(self):
        cfg = ConfigModel.model_construct()
        loaded["loops"] = cfg.loops
        return cfg

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)

    captured = {}

    class DummyOrchestrator:
        def run_query(self, query, config, visualize=None, callbacks=None):
            captured["loops"] = config.loops
            return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    module = importlib.import_module("autoresearch.main.app")
    monkeypatch.setattr(module, "Orchestrator", lambda: DummyOrchestrator())
    main = importlib.import_module("autoresearch.main")

    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "q", "--loops", "4"])
    assert result.exit_code == 0
    assert loaded["loops"] == 2
    assert captured["loops"] == 4


def test_search_help_includes_ontology_flags(monkeypatch, dummy_storage):
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--ontology" in result.stdout
    assert "--ontology-reasoner" in result.stdout
    assert "--infer-relations" in result.stdout


def test_visualize_help_includes_layout(monkeypatch, dummy_storage):
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["visualize", "--help"])
    assert result.exit_code == 0
    assert "--layout" in result.stdout
    assert "--interactive" in result.stdout
    assert "--loops" in result.stdout
    assert "--ontology" in result.stdout
