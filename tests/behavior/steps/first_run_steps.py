# mypy: ignore-errors
# flake8: noqa
from pytest_bdd import scenario, when, then
from typer.testing import CliRunner
import importlib
import typer

from .common_steps import cli_app  # ensure common fixtures are loaded
from autoresearch.config.loader import ConfigLoader

app_mod = importlib.import_module("autoresearch.main.app")


@when("I run the CLI without a config file", target_fixture="no_config_result")
def run_without_config(tmp_path, monkeypatch, cli_runner: CliRunner):
    monkeypatch.chdir(tmp_path)
    loader = ConfigLoader.new_for_tests()
    loader.search_paths = [tmp_path / "missing.toml"]
    loader._update_watch_paths()
    monkeypatch.setattr(app_mod, "_config_loader", loader)
    monkeypatch.setattr(typer, "confirm", lambda *a, **k: False)
    result = cli_runner.invoke(cli_app)
    return result


@then("the welcome banner and initialization prompt are shown")
def check_welcome(no_config_result):
    assert no_config_result.exit_code == 2
    assert "Welcome to Autoresearch!" in no_config_result.stdout
    assert "Would you like to initialize the configuration now?" in no_config_result.stdout
    assert no_config_result.stderr == ""


@when("I run the CLI with an existing config file", target_fixture="with_config_result")
def run_with_config(tmp_path, monkeypatch, cli_runner: CliRunner):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text("[core]\nloops = 1\n")
    loader = ConfigLoader.new_for_tests()
    loader.search_paths = [cfg_path]
    loader._update_watch_paths()
    monkeypatch.setattr(app_mod, "_config_loader", loader)
    result = cli_runner.invoke(cli_app)
    return result


@then("the welcome banner is suppressed")
def check_no_banner(with_config_result):
    assert with_config_result.exit_code == 0
    assert "Welcome to Autoresearch!" not in with_config_result.stdout
    assert with_config_result.stderr == ""


@scenario("../features/first_run.feature", "No config present shows welcome and prompt")
def test_first_run_welcome():
    pass


@scenario("../features/first_run.feature", "Config exists suppresses welcome")
def test_existing_config_suppresses_banner():
    pass
