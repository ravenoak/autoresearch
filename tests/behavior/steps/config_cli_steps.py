from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from typer.testing import CliRunner

from autoresearch.config.loader import ConfigLoader
from autoresearch.main import app as cli_app
from tests.behavior.steps import BehaviorContext, get_cli_result, set_cli_result

from .common_steps import assert_cli_error, assert_cli_success


def pytest_configure(_config: pytest.Config) -> None:  # pragma: no cover - plugin hook
    """Hook required by pytest-bdd for namespace discovery."""


@given("a temporary work directory", target_fixture="work_dir")
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide an isolated working directory for CLI invocations."""

    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()
    return tmp_path


@given("I run `autoresearch config init --force` in a temporary directory")
@when("I run `autoresearch config init --force` in a temporary directory")
def run_config_init(
    work_dir: Path,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Initialize configuration files within a clean directory."""

    _ = work_dir
    result = cli_runner.invoke(cli_app, ["config", "init", "--force"])
    set_cli_result(bdd_context, result)


@when("I run `autoresearch config validate`")
def run_config_validate(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Validate the generated configuration files."""

    result = cli_runner.invoke(cli_app, ["config", "validate"])
    set_cli_result(bdd_context, result)


@when(
    parsers.re(
        r'^I run `autoresearch config reasoning --mode (?P<mode>\w+) --loops (?P<loops>\d+)`$'
    )
)
def run_config_reasoning(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    mode: str,
    loops: int,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Update reasoning configuration with both mode and loops."""

    result = cli_runner.invoke(
        cli_app,
        ["config", "reasoning", "--mode", mode, "--loops", str(loops)],
    )
    set_cli_result(bdd_context, result)


@when(parsers.parse('I run `autoresearch config reasoning --mode {mode}`'))
def run_config_reasoning_mode_only(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    mode: str,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Update reasoning configuration by specifying only the mode."""

    result = cli_runner.invoke(cli_app, ["config", "reasoning", "--mode", mode])
    set_cli_result(bdd_context, result)


@then('the files "autoresearch.toml" and ".env" should be created')
def check_config_files(work_dir: Path) -> None:
    """Ensure initialization produced the expected configuration files."""

    assert (work_dir / "autoresearch.toml").exists()
    assert (work_dir / ".env").exists()


@then("the CLI should exit successfully")
def cli_success(bdd_context: BehaviorContext) -> None:
    """Assert that the CLI invocation succeeded."""

    result = get_cli_result(bdd_context)
    assert_cli_success(result)


@then("the CLI should exit with an error")
def cli_error(bdd_context: BehaviorContext) -> None:
    """Assert that the CLI invocation failed as expected."""

    result = get_cli_result(bdd_context)
    assert_cli_error(result)


@then(parsers.parse('the configuration file should set reasoning mode to "{mode}"'))
def assert_reasoning_mode(work_dir: Path, mode: str) -> None:
    """Confirm the reasoning mode value written to the configuration file."""

    content = (work_dir / "autoresearch.toml").read_text()
    assert f'reasoning_mode = "{mode}"' in content


@then(parsers.parse("the configuration file should set loops to {loops:d}"))
def assert_loops(work_dir: Path, loops: int) -> None:
    """Confirm the reasoning loop count written to the configuration file."""

    content = (work_dir / "autoresearch.toml").read_text()
    assert f"loops = {loops}" in content


@then(parsers.parse('the error message should contain "{text}"'))
def error_message_contains(bdd_context: BehaviorContext, text: str) -> None:
    """Ensure the CLI error message includes the expected text."""

    result = get_cli_result(bdd_context)
    exc = result.exception
    assert exc is not None, "Expected an exception but none occurred"
    assert text in str(exc)


@scenario("../features/config_cli.feature", "Initialize configuration files")
def test_config_init() -> None:
    """Scenario: initialize configuration files."""


@scenario("../features/config_cli.feature", "Validate configuration files")
def test_config_validate() -> None:
    """Scenario: validate generated configuration files."""


@scenario("../features/config_cli.feature", "Update reasoning configuration")
def test_config_reasoning() -> None:
    """Scenario: update reasoning configuration."""


@scenario("../features/config_cli.feature", "Reject invalid reasoning mode")
def test_config_reasoning_invalid() -> None:
    """Scenario: reject invalid reasoning mode inputs."""
