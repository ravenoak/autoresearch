import importlib
import sys
import types

from typer.testing import CliRunner


def test_first_run_detection_respects_search_paths(tmp_path, monkeypatch):
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

    monkeypatch.setattr(ConfigLoader, "load_config", _load)

    main = importlib.import_module("autoresearch.main")

    config_file = tmp_path / "autoresearch.toml"
    config_file.write_text("[core]\nloops = 1\n")

    main._config_loader.search_paths = [config_file]

    runner = CliRunner()
    result = runner.invoke(main.app, ["--help"])
    assert result.exit_code == 0
    assert "Welcome to Autoresearch" not in result.stdout
