import importlib

from typer.testing import CliRunner


def test_first_run_detection_respects_search_paths(
    example_autoresearch_toml, monkeypatch, config_loader, dummy_storage
):

    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "load_config", _load)

    main = importlib.import_module("autoresearch.main")
    app_mod = importlib.import_module("autoresearch.main.app")
    monkeypatch.setattr(app_mod, "_config_loader", config_loader)

    config_file = example_autoresearch_toml

    config_loader.search_paths = [config_file]
    config_loader._update_watch_paths()

    runner = CliRunner()
    result = runner.invoke(main.app, ["--help"])
    assert result.exit_code == 0
    assert "Welcome to Autoresearch" not in result.stdout
