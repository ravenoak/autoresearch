import importlib
import sys
import types
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
    from autoresearch.config import ConfigLoader, ConfigModel

    def _load(self):
        return ConfigModel(loops=1)

    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")
    runner = CliRunner()
    result = runner.invoke(main.app, ["--help"])
    assert result.exit_code == 0
    assert "\x1b[" not in result.stdout
    assert "Usage:" in result.stdout
