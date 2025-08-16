import importlib
from pathlib import Path
from typer.testing import CliRunner


def test_cli_help_no_ansi(dummy_storage, monkeypatch):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(
        ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False
    )
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["--help"])
    assert result.exit_code == 0
    assert "\x1b[" not in result.stdout
    assert "Usage:" in result.stdout


def test_search_help_includes_interactive(dummy_storage, monkeypatch):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(
        ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False
    )
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--interactive" in result.stdout
    assert "--loops" in result.stdout


def test_search_help_includes_visualize(dummy_storage, monkeypatch):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(
        ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False
    )
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--visualize" in result.stdout


def test_search_loops_option(dummy_storage, monkeypatch):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.models import QueryResponse

    loaded = {}

    def _load(self):
        cfg = ConfigModel.model_construct()
        loaded["loops"] = cfg.loops
        return cfg

    monkeypatch.setattr(
        ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False
    )
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)

    captured = {}

    class DummyOrchestrator:
        def run_query(self, query, config, callbacks=None):
            captured["loops"] = config.loops
            return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    import importlib

    module = importlib.import_module("autoresearch.main.app")
    monkeypatch.setattr(module, "Orchestrator", lambda: DummyOrchestrator())
    main = importlib.import_module("autoresearch.main")

    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "q", "--loops", "4"])
    assert result.exit_code == 0
    assert loaded["loops"] == 2
    assert captured["loops"] == 4


def test_search_help_includes_ontology_flags(dummy_storage, monkeypatch):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(
        ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False
    )
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0


def test_visualize_help_includes_layout(dummy_storage, monkeypatch):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(
        ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False
    )
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["visualize", "--help"])
    assert result.exit_code == 0
    assert "--layout" in result.stdout
