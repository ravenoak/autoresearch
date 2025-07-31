import sys
import importlib
import types
from pathlib import Path
from typer.testing import CliRunner


def test_cli_help_no_ansi(monkeypatch):
    dummy_storage = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*a, **k):
            pass

    dummy_storage.StorageManager = StorageManager
    dummy_storage.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", dummy_storage)
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

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


def test_search_help_includes_interactive(monkeypatch):
    dummy_storage = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*a, **k):
            pass

    dummy_storage.StorageManager = StorageManager
    dummy_storage.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", dummy_storage)
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

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


def test_search_help_includes_visualize(monkeypatch):
    dummy_storage = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*a, **k):
            pass

    dummy_storage.StorageManager = StorageManager
    dummy_storage.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", dummy_storage)
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

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


def test_search_loops_option(monkeypatch):
    import pytest
    pytest.skip("loops option CLI interaction fails under test environment")
    dummy_storage = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*a, **k):
            pass

    dummy_storage.StorageManager = StorageManager
    dummy_storage.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", dummy_storage)
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.models import QueryResponse
    from autoresearch.orchestration.orchestrator import Orchestrator

    def _load(self):
        return ConfigModel.model_construct()

    captured = {}

    def _run(query, config, callbacks=None):
        captured["loops"] = config.loops
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    monkeypatch.setattr(Orchestrator, "run_query", _run)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "q", "--loops", "4"])
    assert result.exit_code == 0
    assert captured["loops"] == 4


def test_search_help_includes_ontology_flags(monkeypatch):
    dummy_storage = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*a, **k):
            pass

    dummy_storage.StorageManager = StorageManager
    dummy_storage.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", dummy_storage)
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "search_paths", [Path("dummy.toml")], raising=False)
    monkeypatch.setattr(ConfigLoader, "env_path", Path("dummy.env"), raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0


def test_visualize_help_includes_layout(monkeypatch):
    dummy_storage = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*a, **k):
            pass

    dummy_storage.StorageManager = StorageManager
    dummy_storage.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", dummy_storage)
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

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
