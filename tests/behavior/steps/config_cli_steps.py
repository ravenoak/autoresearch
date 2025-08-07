from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.main import app as cli_app
from autoresearch.config.loader import ConfigLoader


def pytest_configure(config):  # pragma: no cover - silence unused warning
    pass


@given("a temporary work directory", target_fixture="work_dir")
def work_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()
    return tmp_path


@given("I run `autoresearch config init --force` in a temporary directory")
@when("I run `autoresearch config init --force` in a temporary directory")
def run_config_init(work_dir, cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["config", "init", "--force"])
    bdd_context["result"] = result


@when("I run `autoresearch config validate`")
def run_config_validate(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["config", "validate"])
    bdd_context["result"] = result


@when(
    parsers.re(
        r'^I run `autoresearch config reasoning --mode (?P<mode>\w+) --loops (?P<loops>\d+)`$'
    )
)
def run_config_reasoning(cli_runner, bdd_context, mode: str, loops: int):
    result = cli_runner.invoke(
        cli_app, ["config", "reasoning", "--mode", mode, "--loops", str(loops)]
    )
    bdd_context["result"] = result


@when(parsers.parse('I run `autoresearch config reasoning --mode {mode}`'))
def run_config_reasoning_mode_only(cli_runner, bdd_context, mode: str):
    result = cli_runner.invoke(cli_app, ["config", "reasoning", "--mode", mode])
    bdd_context["result"] = result


@then('the files "autoresearch.toml" and ".env" should be created')
def check_config_files(work_dir):
    assert (work_dir / "autoresearch.toml").exists()
    assert (work_dir / ".env").exists()


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@then("the CLI should exit with an error")
def cli_error(bdd_context):
    result = bdd_context["result"]
    assert result.exit_code != 0
    assert result.stderr != ""


@then(parsers.parse('the configuration file should set reasoning mode to "{mode}"'))
def assert_reasoning_mode(work_dir, mode: str):
    content = (work_dir / "autoresearch.toml").read_text()
    assert f'reasoning_mode = "{mode}"' in content


@then(parsers.parse("the configuration file should set loops to {loops:d}"))
def assert_loops(work_dir, loops: int):
    content = (work_dir / "autoresearch.toml").read_text()
    assert f"loops = {loops}" in content


@then(parsers.parse('the error message should contain "{text}"'))
def error_message_contains(bdd_context, text: str):
    exc = bdd_context["result"].exception
    assert exc is not None, "Expected an exception but none occurred"
    assert text in str(exc)


@scenario("../features/config_cli.feature", "Initialize configuration files")
def test_config_init():
    pass


@scenario("../features/config_cli.feature", "Validate configuration files")
def test_config_validate():
    pass


@scenario("../features/config_cli.feature", "Update reasoning configuration")
def test_config_reasoning():
    pass


@scenario("../features/config_cli.feature", "Reject invalid reasoning mode")
def test_config_reasoning_invalid():
    pass
